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
        /* Mobile responsive adjustments */
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

# Sidebar - Search & Controls
st.sidebar.header("Search & Navigation")
query = st.sidebar.text_input("Enter Novel Name or Author:", "Malayalam")

tab1, tab2 = st.tabs(["🔍 Book Index", "📖 Mobile Flip Reader"])


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


if "selected_book" not in st.session_state:
  st.session_state.selected_book = None

# Tab 1: Book Index / Catalog
with tab1:
  st.markdown("### 🔎 Novel Search")
  if query:
    with st.spinner("Searching cloud library..."):
      books = search_open_library(query)

    if books:
      # Mobile grid optimization
      cols = st.columns(2)
      for idx, book in enumerate(books):
        col = cols[idx % 2]
        with col:
          st.image(book["cover"], use_container_width=True)
          st.markdown(f"**{book['title']}**")
          st.caption(f"_{book['author']}_")

          if book["epub_url"] or book["pdf_url"]:
            if st.button("Read Now 📖", key=f"read_{idx}"):
              st.session_state.selected_book = book
              st.success("Selected! Open 'Mobile Flip Reader' tab.")
          else:
            st.info("No online reader available")
          st.divider()
    else:
      st.warning("No downloadable books found.")

# Tab 2: Mobile Viewport 3D Flip Reader
with tab2:
  book = st.session_state.selected_book

  if book:
    st.caption(f"Reading: **{book['title']}** by {book['author']}")

    # Interactive 3D Mobile Reader component (EPUB & PDF JavaScript Engine)
    book_url = book["epub_url"] or book["pdf_url"]
    is_epub = True if book["epub_url"] else False

    # Mobile Full-Viewport HTML/JS Reader Engine
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
                    box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                    cursor: pointer;
                }}
                .btn:active {{
                    transform: scale(0.95);
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
                        transition: "transform 0.3s ease-in-out" // Soft flip transition
                    }});

                    rendition.display();

                    function nextPage() {{ rendition.next(); }}
                    function prevPage() {{ rendition.prev(); }}

                    // Swipe gestures for Mobile
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
                    // Fallback embedded Full Viewport Reader for PDF
                    document.getElementById("area").innerHTML = 
                        '<iframe src="' + bookUrl + '" width="100%" height="100%" style="border:none;"></iframe>';
                }}
            </script>
        </body>
        </html>
        """

    # Embed HTML Reader directly with responsive height
    st.components.v1.html(html_code, height=700, scrolling=False)

  else:
    st.info("Select a novel from the 'Book Index' tab first.")
