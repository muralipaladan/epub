import tempfile
import os
import requests
import streamlit as st
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

st.set_page_config(page_title="Cloud Book Finder & Reader", layout="wide")

st.title("📚 Cloud Novel Finder & Reader")
st.subheader("Free Malayalam/English EPUB & PDF Search & Reader")

# Sidebar - Search & Controls
st.sidebar.header("Search & Navigation")
query = st.sidebar.text_input("Enter Novel Name or Author:", "Malayalam")
language_filter = st.sidebar.selectbox(
    "Filter Language Preference", ["All", "Malayalam", "English"]
)

# Tabs for Search Index and Reading
tab1, tab2 = st.tabs(["🔍 Book Index (Catalog)", "📖 Book Reader"])


def search_open_library(search_query):
  """Fetch free books from Open Library API"""
  url = f"https://openlibrary.org/search.json?q={search_query}"
  try:
    response = requests.get(url, timeout=10)
    data = response.json()
    docs = data.get("docs", [])
    results = []
    for doc in docs[:15]:  # Top 15 results
      title = doc.get("title", "Unknown Title")
      author = doc.get("author_name", ["Unknown Author"])[0]
      cover_i = doc.get("cover_i")
      cover_url = (
          f"https://covers.openlibrary.org/b/id/{cover_i}-M.jpg"
          if cover_i
          else "https://via.placeholder.com/150x200?text=No+Cover"
      )

      # Check available formats or Gutenberg / Archive ID
      gutenberg_id = doc.get("gutenberg_id", [None])[0]
      ia_id = doc.get("ia", [None])[0]

      epub_url = None
      pdf_url = None

      if gutenberg_id:
        epub_url = (
            f"https://www.gutenberg.org/ebooks/{gutenberg_id}.epub.images"
        )
      elif ia_id:
        pdf_url = f"https://archive.org/download/{ia_id}/{ia_id}.pdf"
        epub_url = f"https://archive.org/download/{ia_id}/{ia_id}_epub.epub"

      results.append({
          "title": title,
          "author": author,
          "cover": cover_url,
          "epub_url": epub_url,
          "pdf_url": pdf_url,
      })
    return results
  except Exception as e:
    st.error(f"Error fetching books: {e}")
    return []


# Initialize Session State
if "selected_book" not in st.session_state:
  st.session_state.selected_book = None

with tab1:
  st.markdown("### 🔎 Available Novels Index")
  if query:
    with st.spinner("Searching cloud library..."):
      books = search_open_library(query)

    if books:
      cols = st.columns(3)
      for idx, book in enumerate(books):
        col = cols[idx % 3]
        with col:
          st.image(book["cover"], width=130)
          st.markdown(f"**{book['title']}**")
          st.caption(f"Author: {book['author']}")

          if book["epub_url"] or book["pdf_url"]:
            if st.button("Read Book", key=f"read_{idx}"):
              st.session_state.selected_book = book
              st.success(
                  f"'{book['title']}' selected! Go to 'Book Reader' tab."
              )
          else:
            st.info("Preview / Direct link unavailable")
          st.divider()
    else:
      st.warning("No downloadable books found for this query.")

with tab2:
  st.markdown("### 📖 Novel Reader Zone")
  book = st.session_state.selected_book

  if book:
    st.write(f"### Currently Reading: **{book['title']}**")
    st.write(f"**Author:** {book['author']}")

    # Read EPUB Format
    if book["epub_url"]:
      st.info("Loading EPUB Reader...")
      try:
        res = requests.get(book["epub_url"], timeout=15)
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".epub"
        ) as tmp_file:
          tmp_file.write(res.content)
          tmp_path = tmp_file.name

        epub_book = epub.read_epub(tmp_path)
        chapters = []
        for item in epub_book.get_items():
          if item.get_type() == ebooklib.ITEM_DOCUMENT:
            soup = BeautifulSoup(item.get_content(), "html.parser")
            text = soup.get_text()
            if len(text.strip()) > 100:
              chapters.append(text)

        if chapters:
          chapter_num = st.slider("Select Chapter", 1, len(chapters), 1)
          st.markdown("---")
          st.write(chapters[chapter_num - 1])
        else:
          st.warning("Could not parse EPUB chapters cleanly.")

        os.remove(tmp_path)
      except Exception as e:
        st.error(f"Unable to render EPUB directly: {e}")

    # Read PDF Format
    elif book["pdf_url"]:
      st.info("Loading PDF Viewer...")
      pdf_code = (
          f'<iframe src="{book["pdf_url"]}" width="100%"'
          ' height="700px"></iframe>'
      )
      st.components.v1.html(pdf_code, height=720)

  else:
    st.info("Please select a book from the **Book Index** tab to start reading.")
