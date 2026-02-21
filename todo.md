# 待办事项

## 优化项

- [ ] 使用 LangChain 内置组件重构
  - [x] 文档加载器 → PyPDFLoader, TextLoader 等
  - [ ] 文本分割器 → RecursiveCharacterTextSplitter
  - [ ] Embedding → SentenceTransformerEmbeddings
  - [ ] 向量存储 → Chroma.from_documents
  - [ ] 问答链 → create_retrieval_chain

## 其他

- [x] 添加日志系统
- [ ] 添加缓存机制
- [x] 添加用户界面（Streamlit）
- [ ] 修改引用格式：移除章节，添加行号
- [ ] timeout


可以用第三方包替代的功能
┌───────────────────────┬─────────────────────────────────────────────────┐
│ 当前实现 │ LangChain 内置替代 │
├───────────────────────┼─────────────────────────────────────────────────┤
│ 自定义 PDFLoader │ PyPDFLoader / PDFMinerLoader │
├───────────────────────┼─────────────────────────────────────────────────┤
│ 自定义 DocxLoader │ Docx2txtLoader / UnstructuredWordDocumentLoader │
├───────────────────────┼─────────────────────────────────────────────────┤
│ 自定义 MarkdownLoader │ TextLoader │
├───────────────────────┼─────────────────────────────────────────────────┤
│ 自定义 WebLoader │ WebLoader / UnstructuredURLLoader │
├───────────────────────┼─────────────────────────────────────────────────┤
│ 手写 split_text │ RecursiveCharacterTextSplitter │
├───────────────────────┼─────────────────────────────────────────────────┤
│ 自定义 Embeddings │ SentenceTransformerEmbeddings │
├───────────────────────┼─────────────────────────────────────────────────┤
│ 自定义 VectorStore │ Chroma.from_documents │
├───────────────────────┼─────────────────────────────────────────────────┤
│ 自定义 Retriever │ VectorStoreRetriever │
├───────────────────────┼─────────────────────────────────────────────────┤
│ 自定义 QAChain │ create_retrieval_chain / RetrievalQA │
└───────────────────────┴─────────────────────────────────────────────────┘
