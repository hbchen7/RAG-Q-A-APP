from langchain_text_splitters import RecursiveCharacterTextSplitter
def get_text_splitter(chunk_size:int=500, chunk_overlap:int=50, length_function=len, add_start_index=True ):
  text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=chunk_size, 
    chunk_overlap=chunk_overlap,
    length_function=length_function,
    add_start_index=add_start_index
    )
  return text_splitter