import os
import clip
import torch
import streamlit as st
from PIL import Image
from upstash_vector import Index
from load_data import encode_text
import shutil
import base64
import time

# --- Page Configuration ---
st.set_page_config(
    page_title="Intelligent Image & Text Retrieval System",
    page_icon="🖼️",
    layout="wide"
)

# --- Custom CSS ---
st.markdown("""
<style>
    body, .stApp {
        background-color: #f0f2f6;
    }
    h1 {
        text-align: center;
        color: #2c3e50;
        margin-bottom: 30px;
        font-weight: 600;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        border-bottom: 2px solid #dee2e6;
    }
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        padding: 12px 20px;
        background-color: transparent;
        color: #495057;
        border-radius: 6px 6px 0 0;
        border: none;
        border-bottom: 2px solid transparent;
        transition: all 0.3s ease;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #e9ecef;
        color: #007bff;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ffffff;
        color: #007bff;
        border-color: #007bff;
        box-shadow: 0 -2px 5px rgba(0,0,0,0.05);
    }
    .main-content-columns > div {
        padding: 0px;
    }
    .control-panel, .results-panel {
        padding: 20px;
        border-radius: 8px;
    }

    /* Style for the buttons below result images - make them small and inline */
    .results-container .stButton > button {
        background-color: #007bff;
        color: white;
        border-radius: 6px;
        border: none;
        padding: 5px 10px !important; /* Small padding */
        font-size: 0.8em !important; /* Small font size */
        font-weight: 500;
        margin: 4px 2px !important; /* Small margin to separate */
        cursor: pointer;
        transition: all 0.2s ease-in-out;
        width: auto !important;
        display: inline-block !important;
    }
    .results-container .stButton>button:hover {
        background-color: #0056b3;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        transform: translateY(-1px);
    }
    .results-container .stButton>button:disabled {
        background-color: #ced4da;
        color: #6c757d;
    }
     /* Specific style for the favorited state button */
     .results-container .stButton > button[type="secondary"] {
          background-color: #6c757d !important;
          color: white !important;
     }
     .results-container .stButton > button[type="secondary"]:hover {
          background-color: #5a6268 !important;
          color: white !important;
     }

    /* Style for Text Area and File Uploader for uniformity */
    /* Target based on data-baseweb attribute */
    [data-baseweb="textarea"], [data-baseweb="file-uploader"] > div > div:first-child {
         border: 1px solid #ced4da; /* Standard border color */
         border-radius: 0.25rem; /* Standard border radius */
         padding: 0.75rem 1rem; /* Standard padding */
         background-color: #fff; /* White background */
         margin-bottom: 20px; /* Standard bottom margin */
         box-shadow: inset 0 1px 2px rgba(0,0,0,.075); /* Optional: subtle inset shadow */
         transition: border-color ease-in-out .15s,box-shadow ease-in-out .15s; /* Smooth transition */
    }

    /* Style for focus state */
    [data-baseweb="textarea"]:focus-within, [data-baseweb="file-uploader"]:focus-within > div > div:first-child {
         border-color: #80bdff; /* Highlight color on focus */
         outline: 0; /* Remove default outline */
         box-shadow: 0 0 0 .2rem rgba(0,123,255,.25); /* Glow effect on focus */
    }

    /* Style for the default text/icon inside file uploader if visible */
    /* This might need adjustment based on Streamlit version/structure */
    [data-baseweb="file-uploader"] [data-testid="stFileUploadDropzone"] > div:first-child {
         color: #6c757d; /* Match text color */
         font-size: 1em; /* Match text size */
         margin-bottom: 0.5rem; /* Space below icon/text */
    }
     [data-baseweb="file-uploader"] [data-testid="stFileUploadDropzone"] > div:nth-child(2) {
          color: #6c757d;
          font-size: 0.9em;
     }

    /* Adjust tooltip visibility if needed */
     [data-baseweb="tooltip"] { z-index: 10; } /* Ensure tooltips are above buttons */

    .example-image-container {
        display: flex;
        overflow-x: auto;
        padding-bottom: 15px; 
        gap: 12px;
        margin-top: 10px;
    }
    .example-image-item {
        text-align: center;
        cursor: pointer;
        min-width: 100px;
    }
    .example-image-item img {
        width: 100px; 
        height: 100px; 
        object-fit: cover; 
        border-radius: 6px;
        border: 2px solid #dee2e6;
        margin-bottom: 8px;
        transition: all 0.2s ease-in-out;
    }
     .example-image-item img:hover {
        border-color: #007bff;
        transform: scale(1.05);
        box-shadow: 0 4px 8px rgba(0,123,255,0.3);
    }
    .example-image-item span { 
        font-size: 0.85em;
        color: #495057;
        display: block;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 100px;
    }
    .results-container {
        max-height: 65vh;
        overflow-y: auto;
        padding-right: 10px; 
        margin-top: 10px;
    }
    .stExpander {
        margin-top: 30px;
        background-color: #ffffff;
        border-radius: 8px;
        border: 1px solid #dee2e6;
    }
    .stExpander header {
        font-weight: 500;
        color: #007bff;
    }
    .image-preview-container img {
        border: 2px solid #007bff;
        border-radius: 6px;
        margin-top: 15px;
        max-width: 100%; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .control-panel h3, .results-panel h3, .control-panel h2, .results-panel h2 {
        color: #007bff;
        margin-bottom: 15px;
        border-bottom: 1px solid #e9ecef;
        padding-bottom: 8px;
    }
    .stAlert {
        border-radius: 6px;
        padding: 15px;
    }
    .stAlert p {
        margin-bottom: 0 !important;
    }
</style>
""", unsafe_allow_html=True)

device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)
upstash_index = Index(
    url=os.getenv("UPSTASH_VECTOR_URL"),
    token=os.getenv("UPSTASH_VECTOR_TOKEN")
)

TEMP_QUERY_IMAGE_PATH = "temp_query_image.jpg"
EXAMPLE_IMAGE_DIR = "dataset/examples"

def get_image_as_base64(path):
    try:
        with open(path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        return ""
    except Exception as e:
        return ""

def load_example_images(example_dir):
    if not os.path.isdir(example_dir):
        print(f"Warning: Example directory not found: {example_dir}")
        return []
    supported_extensions = ('.png', '.jpg', '.jpeg')
    return sorted([os.path.join(example_dir, fname) for fname in os.listdir(example_dir)
            if fname.lower().endswith(supported_extensions)])

def query_with_image(query_image_path, top_k=5):
    try:
        query_image = Image.open(query_image_path).convert("RGB")
    except FileNotFoundError:
        st.error(f"Query image not found at path: {query_image_path}")
        return []
    query_tensor = preprocess(query_image).unsqueeze(0).to(device)
    
    with torch.no_grad():
        query_features = model.encode_image(query_tensor)
    query_features = query_features / query_features.norm(dim=-1, keepdim=True)
    
    try:
        results = upstash_index.query(
            vector=query_features.cpu().numpy().flatten().tolist(),
            top_k=top_k,
            include_metadata=True
        )
    except Exception as e:
        st.error(f"Error querying Upstash Vector Index: {e}")
        return []

    return results

def query_with_text(query_text, top_k=5):
    if not query_text.strip():
        st.warning("Please enter some text to search.")
        return []
    encoded_segments, _ = encode_text(query_text)
    if not encoded_segments:
        st.warning("Could not encode the provided text.")
        return []
        
    query_features = encoded_segments[0]
    query_features = query_features / query_features.norm(dim=-1, keepdim=True)

    try:
        results = upstash_index.query(
            vector=query_features.cpu().numpy().flatten().tolist(),
            top_k=top_k,
            include_metadata=True
        )
    except Exception as e:
        st.error(f"Error querying Upstash Vector Index: {e}")
        return []
    print("results",results)
    return results

def display_results_area(results_list):
    if st.session_state.results is None:
        st.info("Search results will appear here. Use the controls on the left to start a new search.")
        return
    
    if hasattr(st.session_state, 'last_search_time'):
        st.success(st.session_state.last_search_time, icon="⏱️")  
        del st.session_state.last_search_time 
    
    if not results_list:
        st.info("No matching images found for your query. Try different keywords or another image.")
        return
    
    st.markdown("""<div class="results-container">""", unsafe_allow_html=True)
    cols_num = st.session_state.get("results_cols", 3)
    
    if cols_num > 1 and len(results_list) < cols_num:
        cols_num = max(1, len(results_list))

    cols = st.columns(cols_num)
    for i, result in enumerate(results_list):
        if 'image_path' in result.metadata:
            image_path = result.metadata['image_path'].replace("\\", "/")
            abs_image_path = os.path.abspath(image_path)
            try:
                with cols[i % cols_num]:
                    st.image(abs_image_path, caption=f"{os.path.basename(abs_image_path)}", use_container_width=True)

                    image_path_to_process = abs_image_path
                    # Use a combination of image path, result ID, and active tab for unique keys
                    # Replace characters that might cause issues in keys
                    unique_key_base = f"{st.session_state.active_tab}_{os.path.basename(image_path_to_process).replace('/', '_').replace('.', '_').replace(' ','_')}_{result.id}"

                    is_favorited = image_path_to_process in st.session_state.favorites
                    favorite_button_label = "❤️ Favorite" if not is_favorited else "✅ Favorited"
                    # Use type="secondary" for favorited state to apply different style
                    # Ensure the key is globally unique
                    if st.button(favorite_button_label, key=f"favorite_{unique_key_base}", use_container_width=False, type="secondary" if is_favorited else "primary"):
                        if not is_favorited:
                            st.session_state.favorites.append(image_path_to_process)
                            st.toast(f"Added {os.path.basename(image_path_to_process)} to favorites!")
                            st.rerun()
                        else:
                             st.session_state.favorites.remove(image_path_to_process)
                             st.toast(f"Removed {os.path.basename(image_path_to_process)} from favorites.")
                             st.rerun()

                    # Download button
                    try:
                        with open(image_path_to_process, "rb") as file:
                            st.download_button(
                                label="⬇️ Download",
                                data=file,
                                file_name=os.path.basename(image_path_to_process),
                                mime="image/jpeg", # Assuming JPEG, adjust if necessary
                                key=f"download_{unique_key_base}", # Ensure the key is globally unique
                                use_container_width=False
                            )
                    except FileNotFoundError:
                        st.warning("Cannot download: File not found.")
                    except Exception as e:
                        st.error(f"Error preparing download: {str(e)}")

            except FileNotFoundError:
                with cols[i % cols_num]:
                    st.warning(f"Img not found: {os.path.basename(abs_image_path)} (Path: {abs_image_path})")
            except Exception as e:
                with cols[i % cols_num]:
                    st.error(f"Error loading {os.path.basename(abs_image_path)}: {str(e)}")
    st.markdown("</div>", unsafe_allow_html=True)

def main():
    st.title("🖼️ Intelligent Image & Text Retrieval System")

    if 'results' not in st.session_state:
        st.session_state.results = None
    if 'query_image_to_show' not in st.session_state:
        st.session_state.query_image_to_show = None
    if 'top_k_slider' not in st.session_state:
        st.session_state.top_k_slider = 6
    if 'results_cols' not in st.session_state:
         st.session_state.results_cols = 3
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = "Image Search"
    if 'favorites' not in st.session_state:
        st.session_state.favorites = []

    tab1_title = "📷 Image Search"
    tab2_title = "✏️ Text Search"
    
    tab1, tab2 = st.tabs([tab1_title, tab2_title])

    with tab1:
        st.session_state.active_tab = tab1_title
        col1, col2 = st.columns([2, 3], gap="medium") 

        with col1:
            st.markdown("<div class='control-panel'>", unsafe_allow_html=True)
            st.subheader("Query by Image")
            uploaded_file = st.file_uploader(
                "Upload an image", 
                type=["jpg", "png", "jpeg"],
                label_visibility="collapsed",
                key="image_uploader"
            )

            if uploaded_file is not None:
                if st.session_state.get('_uploaded_file_id') != uploaded_file.file_id:
                    with open(TEMP_QUERY_IMAGE_PATH, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    st.session_state.query_image_to_show = TEMP_QUERY_IMAGE_PATH
                    st.session_state._uploaded_file_id = uploaded_file.file_id
                    st.session_state.results = None
                    st.rerun()
            
            if st.session_state.query_image_to_show:
                st.markdown("<div class='image-preview-container'>", unsafe_allow_html=True)
                st.image(st.session_state.query_image_to_show, caption="Selected for Query", use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

            b_col1, b_col2 = st.columns(2)
            with b_col1:
                if st.button("Clear Image", key="clear_image", type="secondary", use_container_width=True, disabled=not st.session_state.query_image_to_show):
                    st.session_state.query_image_to_show = None
                    if os.path.exists(TEMP_QUERY_IMAGE_PATH):
                        try:
                            os.remove(TEMP_QUERY_IMAGE_PATH)
                        except OSError as e:
                            st.warning(f"Could not remove temp file: {e}")
                    st.session_state.image_uploader = None 
                    st.session_state.results = None
                    if '_uploaded_file_id' in st.session_state:
                        del st.session_state._uploaded_file_id
                    st.rerun()
            with b_col2:
                search_image_button = st.button("Search with Image", key="search_image", type="primary", use_container_width=True, disabled=not st.session_state.query_image_to_show)
            
            if search_image_button and st.session_state.query_image_to_show:
                start_time = time.time()
                with st.spinner("Searching with image..."):
                    results = query_with_image(st.session_state.query_image_to_show, top_k=st.session_state.top_k_slider)
                end_time = time.time()
                st.session_state.results = results
                st.session_state.last_search_time = f"Search completed in {end_time - start_time:.2f} seconds"

            st.markdown("---")
            st.subheader("✨ Quick Examples")
            example_images = load_example_images(EXAMPLE_IMAGE_DIR)
            if example_images:
                st.markdown("<div class='example-image-container'>", unsafe_allow_html=True)
                num_example_cols = min(len(example_images), 5)
                if num_example_cols > 0:
                    example_display_cols = st.columns(num_example_cols)
                    for idx, ex_img_path in enumerate(example_images):
                        if idx < num_example_cols:
                            with example_display_cols[idx]:
                                base64_image = get_image_as_base64(ex_img_path)
                                if base64_image:
                                     st.markdown(f"""
                                     <div class="example-image-item" style="cursor:pointer;" 
                                          onclick="document.getElementById('select_ex_btn_{idx}').click()">
                                         <img src="data:image/jpeg;base64,{base64_image}" alt="{os.path.basename(ex_img_path)}">
                                         <span>{os.path.basename(ex_img_path)}</span>
                                     </div>
                                     """, unsafe_allow_html=True)
                                     if st.button(f"Select", key=f"select_ex_btn_{idx}", help=f"Use {os.path.basename(ex_img_path)}", type="secondary",
                                                  use_container_width=True):
                                        try:
                                            shutil.copy(ex_img_path, TEMP_QUERY_IMAGE_PATH)
                                            st.session_state.query_image_to_show = TEMP_QUERY_IMAGE_PATH
                                            st.success(f"Selected example: {os.path.basename(ex_img_path)}")
                                            st.session_state.results = None
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Error using example: {e}")
                                else:
                                    st.caption(f"Err:{os.path.basename(ex_img_path)}")
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.caption(f"No example images found in `{EXAMPLE_IMAGE_DIR}`.")
            
            st.session_state.top_k_slider = st.slider(
                "Number of results:", 
                min_value=1, max_value=20, 
                value=st.session_state.top_k_slider, step=1, key="top_k_image_tab"
            )
            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            st.markdown("<div class='results-panel'>", unsafe_allow_html=True)
            st.subheader("Search Results")
            if st.session_state.active_tab == tab1_title:
                display_results_area(st.session_state.results)
            else:
                 st.info("Image search results will appear here.")
            st.markdown("</div>", unsafe_allow_html=True)

    with tab2:
        st.session_state.active_tab = tab2_title
        col1_text, col2_text = st.columns([2, 3], gap="medium")

        with col1_text:
            st.markdown("<div class='control-panel'>", unsafe_allow_html=True)
            st.subheader("Query by Text")
            query_text = st.text_area(
                "Enter your query text:", 
                height=150, 
                placeholder="e.g., a majestic lion in the savanna sunset",
                key="text_input_query"
            )
            
            search_text_button = st.button("Search with Text", key="search_text", type="primary", use_container_width=True, disabled=not query_text.strip())

            if search_text_button and query_text.strip():
                start_time = time.time()
                with st.spinner("Searching with text..."):
                    results = query_with_text(query_text, top_k=st.session_state.top_k_slider)
                end_time = time.time()
                st.session_state.results = results
                st.session_state.last_search_time = f"Search completed in {end_time - start_time:.2f} seconds"

            st.session_state.top_k_slider = st.slider(
                "Number of results:", 
                min_value=1, max_value=20, 
                value=st.session_state.top_k_slider, step=1, key="top_k_text_tab"
            )
            st.markdown("</div>", unsafe_allow_html=True)

        with col2_text:
            st.markdown("<div class='results-panel'>", unsafe_allow_html=True)
            st.subheader("Search Results")
            if st.session_state.active_tab == tab2_title:
                display_results_area(st.session_state.results)
            else:
                st.info("Text search results will appear here.")
            st.markdown("</div>", unsafe_allow_html=True)

    with st.expander("⚙️ Settings & Options", expanded=False):
        st.session_state.results_cols = st.number_input(
            "Columns for results display:", 
            min_value=1, max_value=6, 
            value=st.session_state.results_cols, 
            step=1, key="results_cols_input"
        )
        if st.button("Clear All Results & Query", key="clear_all_results", type="secondary", use_container_width=True):
            st.session_state.results = None
            st.session_state.query_image_to_show = None
            st.session_state.text_input_query = ""
            if os.path.exists(TEMP_QUERY_IMAGE_PATH):
                try:
                    os.remove(TEMP_QUERY_IMAGE_PATH)
                except OSError as e:
                     st.warning(f"Could not remove temp file: {e}")
            st.rerun()
        
        st.caption(f"Temporary image: {TEMP_QUERY_IMAGE_PATH}")
        st.caption(f"Example images from: {EXAMPLE_IMAGE_DIR}")

    with st.expander("❤️ Favorites", expanded=False):
        if not st.session_state.favorites:
            st.info("No favorited images yet. Click the 'Favorite' button on search results to add them here.")
        else:
            st.write(f"You have {len(st.session_state.favorites)} image(s) in your favorites.")
            favorites_cols = st.columns(st.session_state.get("results_cols", 3))

            favorites_list_copy = st.session_state.favorites.copy()

            for j, fav_image_path in enumerate(favorites_list_copy):
                try:
                     with favorites_cols[j % st.session_state.get("results_cols", 3)]:
                         st.image(fav_image_path, caption=f"{os.path.basename(fav_image_path)}", use_container_width=True)

                         # Ensure the key is globally unique and doesn't conflict with search result keys
                         # Key for remove button in favorites - should be unique across all instances
                         remove_button_key = f"remove_fav_{fav_image_path.replace('/', '_').replace('.', '_').replace(' ','_')}"
                         if st.button("Remove from Favorites", key=remove_button_key, use_container_width=True, type="secondary"):
                              if fav_image_path in st.session_state.favorites:
                                   st.session_state.favorites.remove(fav_image_path)
                                   st.toast(f"Removed {os.path.basename(fav_image_path)} from favorites.")
                                   st.rerun()

                except FileNotFoundError:
                     with favorites_cols[j % st.session_state.get("results_cols", 3)]:
                          st.warning(f"Favorited image not found: {os.path.basename(fav_image_path)}")
                except Exception as e:
                     with favorites_cols[j % st.session_state.get("results_cols", 3)]:
                         st.error(f"Error displaying favorited image: {str(e)}")

if __name__ == '__main__':
    if not os.path.exists(EXAMPLE_IMAGE_DIR):
        try:
            os.makedirs(EXAMPLE_IMAGE_DIR)
            st.toast(f"Created example directory: {EXAMPLE_IMAGE_DIR}. Please add some images there for the 'Quick Examples' feature.")
        except OSError as e:
            print(f"Error creating example directory {EXAMPLE_IMAGE_DIR}: {e}")
    main()
