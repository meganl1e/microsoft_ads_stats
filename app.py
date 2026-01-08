import streamlit as st
import pandas as pd
import glob
import os
import io
from urllib.parse import urlparse
import tempfile

# Your exact functions (with minor tweaks for single/multi-file)
def find_header_row(file_content):
    lines = io.StringIO(file_content).readlines()
    for i, line in enumerate(lines):
        if "Event Date,Event Time,URL" in line:
            return i
    return 0

def clean_and_load(file_content):
    try:
        header_row = find_header_row(file_content)
        df = pd.read_csv(io.StringIO(file_content), skiprows=header_row)
        df = df.dropna(subset=['Event Date', 'URL'])
        return df
    except:
        return pd.DataFrame()

def categorize_url(path):
    path = str(path).lower()
    if path == '/' or path == '': return 'Home'
    if '/products' in path: return 'Product'
    if '/recipes' in path: return 'Recipe'
    if '/blogs' in path: return 'Blog'
    if '/cart' in path or 'checkout' in path: return 'Checkout/Cart'
    return 'Other'

def identify_source(url):
    url = str(url).lower()
    if 'msclkid' in url: return 'Microsoft Ads'
    if 'gclid' in url: return 'Google Ads'
    if 'fbclid' in url: return 'Facebook/IG'
    if 'utm_source=ig' in url or 'instagram' in url: return 'Instagram (Organic)'
    if 'utm_source=pinterest' in url: return 'Pinterest'
    if 'utm_source=' in url: return 'Campaign (Other)'
    return 'Direct/Organic'

# Streamlit UI
st.title("Microsoft Ads Stats")
st.write("Upload one or more CSV files → Get cleaned master + reports")

uploaded_files = st.file_uploader("Choose CSV files", accept_multiple_files=True, type='csv')

if uploaded_files:
    df_list = []
    for file in uploaded_files:
        st.info(f"Processing {file.name}...")
        content = file.getvalue().decode('utf-8')
        df = clean_and_load(content)
        if not df.empty:
            df_list.append(df)
    
    if df_list:
        full_df = pd.concat(df_list, ignore_index=True)
        
        # Your exact dedupe + features
        subset_cols = [c for c in ['Event Date', 'Event Time', 'URL', 'Event Action'] if c in full_df.columns]
        full_df.drop_duplicates(subset=subset_cols, inplace=True)
        
        full_df['clean_path'] = full_df['URL'].apply(lambda x: urlparse(str(x)).path)
        full_df['Category'] = full_df['clean_path'].apply(categorize_url)
        full_df['Source'] = full_df['URL'].apply(identify_source)
        
        # Show preview
        st.subheader("✅ Cleaned Data Preview")
        st.dataframe(full_df.head(1000))
        
        # Reports
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Traffic Sources")
            st.dataframe(full_df['Source'].value_counts())
        with col2:
            st.subheader("Top Categories")
            st.dataframe(full_df['Category'].value_counts())
        
        # Download button
        csv = full_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "💾 Download Master CSV",
            csv,
            "master_dataset_cleaned.csv",
            "text/csv"
        )
    else:
        st.warning("No valid data found in files.")



