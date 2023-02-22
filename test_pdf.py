import fitz


def get_text_percentage(file_name: str) -> float:
    """
    Calculate the percentage of document that is covered by (searchable) text.

    If the returned percentage of text is very low, the document is
    most likely a scanned PDF
    """
    total_page_area = 0.0
    total_text_area = 0.0

    doc = fitz.open(file_name)

    for page_num, page in enumerate(doc):
        total_page_area = total_page_area + abs(page.rect)
        text_area = 0.0
        for b in page.getTextBlocks():
            r = fitz.Rect(b[:4])  # rectangle where block text appears
            text_area = text_area + abs(r)
        total_text_area = total_text_area + text_area
    doc.close()
    text_perc = total_text_area / total_page_area
    if text_perc < 0.01:
        return True
    else:
        return False

if __name__ == "__main__":
    text_perc = get_text_percentage("./0ad7c59bcec2426b81c9b87676b4e4b5_ngodong1.pdf")
    print(text_perc)
