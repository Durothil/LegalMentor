from transformers import LayoutLMv2Processor
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
import re

from langchain_core.documents import Document as LCDocument
from sentence_transformers import SentenceTransformer, util
from typing import List


# ======== MODELOS =========
# LayoutLMv2
processor = LayoutLMv2Processor.from_pretrained("microsoft/layoutlmv2-base-uncased")

# Sentence-BERT (MiniLM para agrupamento semântico)
semantic_model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")


# ======== ETAPA 1: OCR + Estrutura Visual ========
def image_to_layout_chunks(image: Image.Image, page_number: int = 1) -> List[LCDocument]:
    """
    Aplica OCR com bounding boxes e LayoutLMv2 para estruturar o conteúdo.
    """
    width, height = image.size
    ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT, lang="por")

    words, boxes = [], []

    for i in range(len(ocr_data['text'])):
        word = ocr_data['text'][i]
        if word.strip():
            words.append(word)
            (x, y, w, h) = (ocr_data['left'][i], ocr_data['top'][i], ocr_data['width'][i], ocr_data['height'][i])
            boxes.append([
                int(1000 * x / width),
                int(1000 * y / height),
                int(1000 * (x + w) / width),
                int(1000 * (y + h) / height),
            ])

    if not words:
        return []

    encoding = processor(image, words=words, boxes=boxes, return_tensors="pt", truncation=True, padding="max_length")

    # Agrupamento por linhas
    lines = {}
    for i, line_num in enumerate(ocr_data["line_num"]):
        if ocr_data["text"][i].strip():
            lines.setdefault(line_num, []).append(ocr_data["text"][i])

    documents = []
    for line_num, words in lines.items():
        line_text = " ".join(words)
        documents.append(
            LCDocument(page_content=line_text.strip(), metadata={"page": page_number, "line": line_num})
        )

    # Etapa 2: Regex para separação jurídica
    return split_legal_chunks_regex(documents)


# ======== ETAPA 2: Regex Jurídico ========
def split_legal_chunks_regex(documents: List[LCDocument]) -> List[LCDocument]:
    """
    Divide chunks maiores em trechos jurídicos com base em padrões (CLÁUSULAS, ARTs, §§, etc).
    """
    pattern = re.compile(
        r"(CLÁUSULA\s+\w+.*?|Art\.\s*\d+º?.*?|§\s*\d+º?.*?|Parágrafo\s+único.*?|[IVXLCDM]+\s*-\s+.*?|[a-zA-Z]\))",
        flags=re.IGNORECASE,
    )

    new_chunks = []

    for doc in documents:
        content = doc.page_content
        matches = list(pattern.finditer(content))

        if not matches:
            new_chunks.append(doc)
            continue

        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            chunk_text = content[start:end].strip()

            if len(chunk_text) > 20:
                new_chunks.append(
                    LCDocument(page_content=chunk_text, metadata=doc.metadata)
                )

    return new_chunks


# ======== ETAPA 3: Agrupamento Semântico ========
def adaptive_similarity_threshold(chunk_text: str) -> float:
    """
    Retorna um limiar de similaridade baseado no tamanho do texto.
    Chunks curtos exigem mais similaridade; chunks longos, um pouco menos.
    """
    return 0.80 if len(chunk_text) < 300 else 0.70

def group_similar_chunks(chunks: List[LCDocument]) -> List[LCDocument]:
    """
    Agrupa chunks juridicamente próximos com base em similaridade semântica adaptativa.
    """
    grouped_chunks = []
    if not chunks:
        return grouped_chunks

    current_text = chunks[0].page_content
    current_meta = chunks[0].metadata
    current_embedding = semantic_model.encode(current_text, convert_to_tensor=True)

    for i in range(1, len(chunks)):
        next_text = chunks[i].page_content
        next_embedding = semantic_model.encode(next_text, convert_to_tensor=True)
        similarity = util.cos_sim(current_embedding, next_embedding).item()

        if similarity >= adaptive_similarity_threshold(current_text):
            current_text += "\n" + next_text
        else:
            grouped_chunks.append(LCDocument(page_content=current_text.strip(), metadata=current_meta))
            current_text = next_text
            current_meta = chunks[i].metadata
            current_embedding = next_embedding

    grouped_chunks.append(LCDocument(page_content=current_text.strip(), metadata=current_meta))
    return grouped_chunks


# ======== Função Principal ========
def layout_ocr_from_pdf(file_path: str) -> List[LCDocument]:
    """
    Converte um PDF imagem em chunks estruturados com OCR + LayoutLM + Regex + Agrupamento semântico.
    """
    pages = convert_from_path(file_path, dpi=300)
    all_chunks = []

    for i, page in enumerate(pages):
        page_chunks = image_to_layout_chunks(page, page_number=i + 1)
        all_chunks.extend(page_chunks)

    # Final: agrupar semanticamente
    return group_similar_chunks(all_chunks)
