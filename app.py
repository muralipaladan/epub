import tempfile
import os
import requests
import streamlit as st

# Mobile-first Viewport Page Config
st.set_page_config(
    page_title="Cloud Book Reader",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom Mobile CSS styling
st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 0rem !important;
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
        }
        iframe {
            border: none !important;
            width: 100% !important;
            border-radius: 8px;
        }
        @media (max-width: 768px) {
            .stButton>button {
                width: 100%;
                margin-bottom: 5px;
            }
        }
    </style>
""",
    unsafe_allow_html=True,
)

st.title("📚 Mobile Cloud Reader")

# Sidebar - Multi-Source Search & Controls
st.sidebar.header("🔍 Search & Settings")
query = st.sidebar.text_input("Enter Book Title, Author or Keyword:", "Malayalam Novel")
search_engine = st.sidebar.radio("Select Search Source:", ["Google Books", "Open Library"])

tab1, tab2 = st.tabs(["🔍 Book Search Index", "📖 Mobile Flip Reader"])


def search_google_books(search_query):
    """Fetch free/preview books from Google Books API"""
    url = f"https://www.googleapis.com/books/v1/volumes?q={search_query}&maxResults=15"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        items = data.get("items", [])
        results = []
        for item in items:
            volume_info = item.get("volumeInfo", {})
            access_info = item.get("accessInfo", {})

            title = volume_info.get("title", "Unknown Title")
            authors = volume_info.get("authors", ["Unknown Author"])
            author = ", ".join(authors)

            image_links = volume_info.get("imageLinks", {})
            cover_url = image_links.get("thumbnail") or image_links.get("smallThumbnail") or "https://via.placeholder.com/150x200?text=No+Cover"

            epub_download = access_info.get("epub", {}).get("downloadLink")
            pdf_download = access_info.get("pdf", {}).get("downloadLink")
            web_reader_link = access_info.get("webReaderLink")

            # Fallback EPUB/PDF URL logic
            epub_url = epub_download if access_info.get("epub", {}).get("isAvailable") else None
            pdf_url = pdf_download if access_info.get("pdf", {}).get("isAvailable") else web_reader_link

            results.append({
                "title": title,
                "author": author,
                "cover": cover_url,
                "epub_url": epub_url,
                "pdf_url": pdf_url,
                "reader_link": web_reader_link
            })
        return results
    except Exception as e:
        st.error(f"Google Books search error: {e}")
        return []


def search_open_library(search_query):
    """Fetch free books from Open Library API"""
    url = f"https://openlibrary.org/search.json?q={search_query}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        docs = data.get("docs", [])
        results = []
        for doc in docs[:15]:
            title = doc.get("title", "Unknown Title")
            author = doc.get("author_name", ["Unknown Author"])[0]
            cover_i = doc.get("cover_i")
            cover_url = (
                f"https://covers.openlibrary.org/b/id/{cover_i}-M.jpg"
                if cover_i
                else "https://via.placeholder.com/150x200?text=No+Cover"
            )

            gutenberg_id = doc.get("gutenberg_id", [None])[0]
            ia_id = doc.get("ia", [None])[0]

            epub_url = None
            pdf_url = None

            if gutenberg_id:
                epub_url = f"https://www.gutenberg.org/ebooks/{gutenberg_id}.epub.images"
            elif ia_id:
                pdf_url = f"https://archive.org/download/{ia_id}/{ia_id}.pdf"
                epub_url = f"https://archive.org/download/{ia_id}/{ia_id}_epub.epub"

            results.append({
                "title": title,
                "author": author,
                "cover": cover_url,
                "epub_url": epub_url,
                "pdf_url": pdf_url,
                "reader_link": pdf_url or epub_url
            })
        return results
    except Exception as e:
        st.error(f"Open Library search error: {e}")
        return []


if "selected_book" not in st.session_state:
    st.session_state.selected_book = None

# Tab 1: Book Search Index
with tab1:
    st.markdown(f"### 🔎 Search Results from **{search_engine}**")
    if query:
        with st.spinner("Searching internet/cloud library..."):
            if search_engine == "Google Books":
                books = search_google_books(query)
            else:
                books = search_open_library(query)

        if books:
            cols = st.columns(2)
            for idx, book in enumerate(books):
                col = cols[idx % 2]
                with col:
                    st.image(book["cover"], use_container_width=True)
                    st.markdown(f"**{book['title']}**")
                    st.caption(f"_{book['author']}_")

                    if book["epub_url"] or book["pdf_url"] or book["reader_link"]:
                        if st.button("Read Now 📖", key=f"read_{idx}"):
                            st.session_state.selected_book = book
                            st.success("Selected! Open 'Mobile Flip Reader' tab.")
                    else:
                        st.info("No online view available")
                    st.divider()
        else:
            st.warning("No downloadable books found for this query.")

# Tab 2: Mobile 3D Flip Reader Mode
with tab2:
    book = st.session_state.selected_book

    if book:
        st.caption(f"Reading: **{book['title']}** by {book['author']}")

        book_url = book["epub_url"] or book["pdf_url"] or book["reader_link"]
        is_epub = True if book["epub_url"] else False

        html_code = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
            <script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.1.5/jszip.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/epubjs/dist/epub.min.js"></script>
            <style>
                body {{
                    margin: 0;
                    padding: 0;
                    background-color: #f4f1ea;
                    font-family: sans-serif;
                    overflow: hidden;
                }}
                #reader-container {{
                    width: 100vw;
                    height: 80vh;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                }}
                #area {{
                    width: 100%;
                    height: 100%;
                    box-shadow: 0 4px 10px rgba(0,0,0,0.15);
                    background: #fff;
                }}
                .controls {{
                    position: fixed;
                    bottom: 10px;
                    left: 0;
                    right: 0;
                    display: flex;
                    justify-content: space-around;
                    padding: 8px 15px;
                    background: rgba(255, 255, 255, 0.95);
                    border-top: 1px solid #ddd;
                    z-index: 100;
                }}
                .btn {{
                    background: #2b580c;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 20px;
                    font-weight: bold;
                    font-size: 14px;
                    cursor: pointer;
                }}
            </style>
        </head>
        <body>
            <div id="reader-container">
                <div id="area"></div>
            </div>

            <div class="controls">
                <button class="btn" onclick="prevPage()">◀ Prev</button>
                <button class="btn" onclick="nextPage()">Next ▶</button>
            </div>

            <script>
                var bookUrl = "{book_url}";
                var isEpub = {str(is_epub).lower()};

                if (isEpub) {{
                    var book = ePub(bookUrl);
                    var rendition = book.renderTo("area", {{
                        width: "100%",
                        height: "100%",
                        transition: "transform 0.3s ease-in-out"
                    }});
                    rendition.display();

                    function nextPage() {{ rendition.next(); }}
                    function prevPage() {{ rendition.prev(); }}

                    var startX = 0;
                    document.getElementById("area").addEventListener("touchstart", function(e) {{
                        startX = e.touches[0].clientX;
                    }});
                    document.getElementById("area").addEventListener("touchend", function(e) {{
                        var endX = e.changedTouches[0].clientX;
                        if (startX - endX > 50) nextPage();
                        if (endX - startX > 50) prevPage();
                    }});
                }} else {{
                    document.getElementById("area").innerHTML = 
                        '<iframe src="' + bookUrl + '" width="100%" height="100%" style="border:none;"></iframe>';
                }}
            </script>
        </body>
        </html>
        """

        st.components.v1.html(html_code, height=700, scrolling=False)
    else:
        st.info("Select a book from the 'Book Search Index' tab first.")
