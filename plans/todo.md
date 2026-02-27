# 待办事项

## 优化项

- [x] 使用 LangChain 内置组件重构
  - [x] 文档加载器 → PyPDFLoader, TextLoader 等
  - [x] 文本分割器 → RecursiveCharacterTextSplitter
  - [x] Embedding → SentenceTransformerEmbeddings
  - [ ] 向量存储 → Chroma.from_documents, 改为自研
  - [ ] 问答链 → create_retrieval_chain, 改为自研

## 其他

- [x] 添加日志系统
- [ ] 添加缓存机制
- [x] 添加用户界面（Streamlit）
- [ ] 修改引用格式：移除章节，添加行号
- [ ] timeout

3. Query Expansion (查询扩展)

- 改写用户查询
- 生成多个相似查询并行检索
- 适合用户表述不清晰的场景
