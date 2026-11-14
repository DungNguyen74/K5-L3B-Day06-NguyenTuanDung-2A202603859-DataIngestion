# Báo cáo cá nhân — Day 6: Data Ingestion Engineering

> **Học viên:** Nguyễn Tuấn Dũng | **MSSV:** 2A202603859 | **Lớp:** L3B  
> **Dự án:** Xây dựng Pipeline Ingestion, Chunking, Vector Indexing và Đánh giá Benchmark cho Báo cáo Thường niên Ngân hàng Thế giới (World Bank Annual Reports)  
> **Ngày hoàn thành:** 14/11/2026  

---

## 1. Dữ liệu và pipeline

### Chủ đề, nguồn/quyền, số trang và quy tắc tính trang
- **Chủ đề:** Báo cáo Tài chính và Phát triển Kinh tế Thường niên của Nhóm Ngân hàng Thế giới (World Bank Group Annual Reports).
- **Nguồn tài liệu & Bản quyền:** 
  - Toàn bộ dữ liệu được tải từ kho mở chính thức **World Bank Open Knowledge Repository (OKR)**:
    - *World Bank Annual Report 2024*: [Handle 10986/42057](https://openknowledge.worldbank.org/handle/10986/42057), tệp `data/world_bank_annual_report_2024.pdf`.
    - *World Bank Annual Report 2023*: [Handle 10986/40219](https://openknowledge.worldbank.org/handle/10986/40219), tệp `data/world_bank_annual_report_2023.pdf`.
  - Giấy phép phân phối: **Creative Commons Attribution 3.0 IGO (CC-BY 3.0 IGO)** — cho phép khai thác, sao chép và xử lý học thuật hợp pháp.
- **Số trang và quy tắc tính trang:**
  - Tổng số trang vật lý của hai tài liệu: 46 trang (báo cáo 2024) + 114 trang (báo cáo 2023) = 160 trang vật lý.
  - **Quy tắc tính trang:** Chỉ tính các trang chứa nội dung thực tế (độ dài ký tự văn bản sau chuẩn hóa $> 50$ ký tự).
  - **Trang loại trừ:** Các trang bìa không có chữ, trang phân cách, và các trang phụ lục trắng kỹ thuật không chứa nội dung phân tích (tổng cộng loại trừ 4 trang).
  - **Tổng số trang nội dung hợp lệ:** **156 trang** (vượt xa ngưỡng tối thiểu $\ge 30$ trang theo quy định của Checkpoint 0:25).

### Chuẩn hóa, lỗi và giới hạn
- **Quy trình chuẩn hóa văn bản (`starter/src/ingestion.py`):**
  - Chuyển đổi toàn bộ văn bản về dạng chuẩn hóa Unicode NFC (`unicodedata.normalize('NFC', text)`).
  - Nối các từ bị ngắt dòng do dấu gạch nối cuối dòng (`re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)`).
  - Xử lý ký tự đặc biệt, chuyển đổi các dấu gạch ngang dài (`—`, `–`) về gạch ngang tiêu chuẩn, loại bỏ khoảng trắng không ngắt (`\u00a0`).
  - Hợp nhất các chuỗi khoảng trắng và dấu xuống dòng thừa thành định dạng văn bản chuẩn.
- **Ghi nhận lỗi & Phương án xử lý (Error Handling):**
  - *Sự cố tệp quét ảnh ban đầu:* Hai tệp người dùng nạp ban đầu (`adb-annual-report-2025.pdf` và `THE-WORLD-BANK-GROUP-ANNUAL-REPORT-2026.pdf`) là bản scan 100% hình ảnh không có text layer (0 ký tự văn bản trích xuất). Pipeline đã tự động phát hiện, ghi log cảnh báo và chuyển hai tệp quét vào thư mục lưu trữ `data/scanned_archive/`, đồng thời kích hoạt việc nạp hai bản PDF digital nguyên bản có selectable text layer từ World Bank OKR.
  - *Sự cố Drop-caps:* Trong báo cáo World Bank, một số chữ cái đầu đoạn (drop-caps) bị pypdf tách thành ký tự đơn trên dòng riêng (ví dụ: `T\nhe`, `D\neeply`). Pipeline đã chuẩn hóa để giữ tính toàn vẹn của từ vựng.
- **Giới hạn của dữ liệu trích xuất:**
  - Bảng biểu số liệu phức tạp và đồ thị Infographic dạng vector đôi khi bị mất cấu trúc hàng/cột khi trích xuất qua `pypdf`, văn bản được chuyển thành luồng tuyến tính.

### Embedding model/provider/version/số chiều, vector store/version, metric, lệnh chạy và chi phí
- **Embedding Model & Provider:**
  - **Mô hình chính thức sử dụng:** `all-MiniLM-L6-v2` (Sentence-Transformers / HuggingFace, triển khai qua ONNX Runtime cục bộ `fastembed`).
  - **Số chiều (Dimensions):** 384 chiều.
  - **Khoảng cách vector (Distance Metric):** Cosine Space (`hnsw:space: cosine`).
  - **Ghi nhận sự cố Provider & Phương án dự phòng (Fallback theo đúng RULES.md):**
    - Ban đầu pipeline đã tích hợp và cấu hình Google Gemini API (`gemini-embedding-001`, 768 chiều). Tuy nhiên, trên tài khoản Free Tier cá nhân, hạn ngạch (quota) giới hạn nghiêm ngặt ở mức 100 RPM / 30.000 TPM. Khi embedding 1.202 chunks của Strategy A, API trả về lỗi `HTTP 429 Resource Exhausted` sau ~880 chunks.
    - Căn cứ theo quy định tại `RULES.md` (*"Khi gặp lỗi provider, quota... ghi lại lỗi và nêu đúng phương án dự phòng đã dùng"*) và `GUIDE.md` (*"Nếu thiết lập chậm, dùng embedding model local"*), hệ thống đã kích hoạt phương án dự phòng chuyển sang mô hình local ONNX `all-MiniLM-L6-v2`. Mô hình chạy 100% offline, embedding toàn bộ 2.249 chunks chỉ trong ~67 giây mà không phát sinh bất kỳ lỗi rate limit nào.
- **Vector Store:**
  - **Loại:** `ChromaDB` phiên bản `1.5.9`.
  - **Cơ chế lưu trữ:** `chromadb.PersistentClient` lưu dữ liệu ổn định tại thư mục `starter/chroma_data/`.
  - **Tính năng:** Tự động hỗ trợ HNSW index, metadata filtering (`$and`, `$eq`), và idempotent upserts chống trùng lặp dữ liệu.
- **Lệnh chạy tái lập pipeline:**
  ```powershell
  python starter/src/run.py
  ```
- **Chi phí phát sinh:** **0.00 USD** (sử dụng tài nguyên local ONNX mã nguồn mở và ChromaDB persistent local).

### Metadata bắt buộc, trường lọc bổ sung, nguồn giá trị và lý do chọn
- **Trường bắt buộc:**
  - `document_id` (hoặc `doc_id`): Mã định danh tài liệu (`wb_annual_report_2024`, `wb_annual_report_2023`).
  - `source`: Đường dẫn tương đối đến tệp nguồn PDF.
  - `page`: Số trang vật lý trích xuất trong tệp PDF.
  - `year`: Năm phát hành của báo cáo tài chính (`2024` hoặc `2023`).
- **Trường lọc bổ sung (Custom Metadata):**
  - `institution`: Cơ quan phát hành (`WBG` - World Bank Group).
  - `chunk_strategy`: Chiến lược phân đoạn (`fixed_size` hoặc `by_paragraph`).
  - `chunk_index`: Vị trí tương đối của chunk trong trang.
- **Nguồn giá trị và Lý do chọn:**
  - Nguồn giá trị được gán có cấu trúc tại bước `load_pdf` thông qua tệp kê khai `data/manifest.json`.
  - *Lý do chọn:* Báo cáo tài chính thường có các chỉ số kinh tế lặp lại theo từng năm (ví dụ cam kết tài chính, số vốn IBRD/IDA). Việc gắn metadata `year` và `institution` cho phép hệ thống RAG thực thi điều kiện lọc chính xác tuyệt đối, tránh hiện tượng nhầm lẫn số liệu giữa các năm tài chính khác nhau.

---

## 2. Cấu hình và benchmark

### A / B / C (tham số cụ thể, khác biệt duy nhất B–C)
- **Chiến lược A (Fixed-size Chunking):**
  - Cắt văn bản theo kích thước ký tự cố định: `chunk_size = 500` ký tự, `overlap = 50` ký tự.
  - Cơ chế: Cắt trượt không nhận biết cấu trúc đoạn/câu.
  - Tổng số chunk sinh ra trên toàn corpus: **1.202 chunks**.
- **Chiến lược B (Paragraph-aware Chunking):**
  - Cắt văn bản theo ranh giới đoạn văn tự nhiên (phân cách bởi dấu xuống dòng `\n\n`), ngưỡng kích thước tối đa: `max_size = 600` ký tự, `overlap = 0`.
  - Cơ chế: Bảo toàn nguyên vẹn ngữ nghĩa của từng đoạn văn; các đoạn ngắn liền kề được ghép lại nếu tổng chiều dài $< 600$ ký tự.
  - Tổng số chunk sinh ra trên toàn corpus: **1.047 chunks**.
- **Chiến lược C (Paragraph-aware + Metadata Filter):**
  - Cấu trúc chunking: Hoàn toàn giống Chiến lược B (`by_paragraph`, `max_size = 600`, `overlap = 0`, dùng chung 1.047 chunks và cùng một vector index trong ChromaDB).
  - **Khác biệt duy nhất giữa B và C:** Khi truy vấn, Chiến lược C kích hoạt bộ lọc metadata (`where={"year": ...}`) tương ứng với phạm vi năm của câu hỏi (được xác định trước trong metadata filter của câu hỏi benchmark), trong khi Chiến lược B thực hiện tìm kiếm toàn văn trên toàn bộ kho vector.

### ≥20 câu: phân chia ≥15 dev / ≥5 test, câu metadata filter và cách kiểm chứng evidence
- **Quy mô tập dữ liệu Benchmark:**
  - Tổng số câu hỏi: **20 câu hỏi** (được lưu tại `benchmark/questions.json`).
  - Phân chia: **15 câu Dev** (`q01` đến `q15`) và **5 câu Test** (`q16` đến `q20`).
  - Tỉ lệ phân chia: 75% Dev / 25% Test (đáp ứng đúng tiêu chuẩn $\ge 15$ dev / $\ge 5$ test).
- **Phân loại câu hỏi & Câu có Filter:**
  - 10 câu hỏi sự kiện trực tiếp (`truc_tiep`).
  - 6 câu hỏi tổng hợp/suy luận/phạm vi rộng (`tong_hop`).
  - 4 câu hỏi có điều kiện lọc metadata bắt buộc (`filter`):
    - `q03` (dev, filter: `{"year": 2024}`)
    - `q07` (dev, filter: `{"year": 2024}`)
    - `q10` (dev, filter: `{"year": 2023}`)
    - `q18` (test, filter: `{"year": 2023}`) — đảm bảo có ít nhất 1 câu filter trong tập test.
- **Cách kiểm chứng Evidence Quote:**
  - 100% cả 20 câu hỏi đều có trường `evidence_quote` trích xuất nguyên văn từng từ từ trang tài liệu chuẩn (`gold_page`).
  - Tính chính xác được xác minh tự động bằng thuật toán so khớp chuỗi chuẩn hóa `is_chunk_a_hit()` trong `starter/src/evaluation.py` trước khi đưa vào benchmark.

### Tiêu chí chọn chiến lược đã chốt trước khi xem test
- **Nguyên tắc đóng băng (Frozen Decision Criteria):** Được chốt trước khi chạy đánh giá trên tập Test nhằm đảm bảo tính khách quan khoa học:
  1. **Tiêu chí định lượng tiên quyết:** Chiến lược phải đạt **Evidence Hit@3 trên tập Dev $\ge 80.0\%$**.
  2. **Tiêu chí định tính chất lượng:** Điểm tính mạch lạc (**Chunk Coherence**) qua audit thủ công phải đạt $\ge 1.5/2.0$.
  3. **Tiêu chí lọc:** Khả năng tuân thủ điều kiện lọc metadata đạt $100\%$ không gây lỗi suy giảm kết quả.
  - *Dự đoán tiên nghiệm:* Chiến lược C (Paragraph-aware + Metadata Filter) sẽ là chiến lược tối ưu nhất.

---

## 3. Kết quả

### Bảng kết quả định lượng (Quantitative Metrics)

| Strategy | Split | Hit@1 (n/N) | Evidence Hit@3 (n/N) | Chunk count | Thời gian chạy (s) | Chi phí |
|---|---|---|---|---|---|---|
| **Strategy A** (Fixed 500/50) | **Dev** | 9/15 (60.0%) | 11/15 (73.3%) | 1.202 | 0.06s | 0 USD |
| **Strategy A** (Fixed 500/50) | **Test** | 2/5 (40.0%) | 2/5 (40.0%) | 1.202 | 0.01s | 0 USD |
| **Strategy B** (Paragraph 600) | **Dev** | 8/15 (53.3%) | **13/15 (86.7%)** | 1.047 | 0.04s | 0 USD |
| **Strategy B** (Paragraph 600) | **Test** | 2/5 (40.0%) | 2/5 (40.0%) | 1.047 | 0.01s | 0 USD |
| **Strategy C** (Paragraph + Filter)| **Dev** | 8/15 (53.3%) | **13/15 (86.7%)** | 1.047 | 0.05s | 0 USD |
| **Strategy C** (Paragraph + Filter)| **Test** | 2/5 (40.0%) | 2/5 (40.0%) | 1.047 | 0.01s | 0 USD |

### Bảng kết quả audit chất lượng thủ công (Manual Quality Audits)

| Strategy | Coherence trung bình /2 (n=10) | Metadata đủ và đúng (n/N) | Filter tuân thủ (n/N) | Grounding 0/1/2 (số câu) và trung bình /2 |
|---|---|---|---|---|
| **Strategy A** | 0.20 / 2.0 (n=10) | 15 / 15 (100%) | N/A | [Chỉ audit chuyên sâu trên cấu hình B/C] |
| **Strategy B** | **1.80 / 2.0** (n=10) | 15 / 15 (100%) | N/A | 0: 12 chunk \| 1: 1 chunk \| 2: 2 chunk (TB: 0.33/2.0) |
| **Strategy C** | **1.80 / 2.0** (n=10) | 15 / 15 (100%) | **3 / 3 (100%)** | 0: 12 chunk \| 1: 1 chunk \| 2: 2 chunk (TB: 0.33/2.0) |

### Đường dẫn trace, nhãn thủ công và cách chọn mẫu
- **Đường dẫn tệp trace kết quả:**
  - Trace Strategy A: [`results/traces_strategy_a.json`](file:///c:/Users/reals/Vin/K5-L3-Day06-DataIngestionEngineering/results/traces_strategy_a.json)
  - Trace Strategy B: [`results/traces_strategy_b.json`](file:///c:/Users/reals/Vin/K5-L3-Day06-DataIngestionEngineering/results/traces_strategy_b.json)
  - Trace Strategy C: [`results/traces_strategy_c.json`](file:///c:/Users/reals/Vin/K5-L3-Day06-DataIngestionEngineering/results/traces_strategy_c.json)
  - Nhật ký thực nghiệm: [`artifacts/experiment_log.csv`](file:///c:/Users/reals/Vin/K5-L3-Day06-DataIngestionEngineering/artifacts/experiment_log.csv)
  - Tóm tắt tổng hợp: [`results/benchmark_summary.json`](file:///c:/Users/reals/Vin/K5-L3-Day06-DataIngestionEngineering/results/benchmark_summary.json)
- **Đường dẫn tệp audit nhãn thủ công:**
  - Audit Chunk Coherence: [`results/manual_audit_coherence.json`](file:///c:/Users/reals/Vin/K5-L3-Day06-DataIngestionEngineering/results/manual_audit_coherence.json)
  - Audit Grounding & Metadata: [`results/manual_audit_grounding.json`](file:///c:/Users/reals/Vin/K5-L3-Day06-DataIngestionEngineering/results/manual_audit_grounding.json)
- **Phương pháp chọn mẫu audit khách quan:**
  - *Chunk Coherence:* Chọn 10 vị trí trang trải đều, cố định trên toàn bộ hai tài liệu (Báo cáo 2024: trang 4, 10, 16, 25, 38; Báo cáo 2023: trang 5, 20, 45, 75, 100). Đánh giá tính toàn vẹn của chunk tại cùng vị trí đó giữa Chiến lược A và B theo thang điểm chuẩn 0 / 1 / 2.
  - *Metadata & Grounding Quality:* Lấy toàn bộ 5 câu hỏi trong tập Test $\times$ 3 chunk trả về trong Top-3 = 15 bản ghi độc lập, kiểm tra chéo với văn bản gốc.

---

## 4. Phân tích và kết luận

### So sánh A–B và B–C; 2 ví dụ sai có ID câu và nguồn
1. **So sánh Chiến lược A (Fixed) và B (Paragraph):**
   - *Hiệu quả truy xuất:* Chiến lược B vượt trội rõ rệt trên tập Dev với **Evidence Hit@3 đạt 86.7% (13/15)** so với **73.3% (11/15)** của Chiến lược A.
   - *Độ mạch lạc văn bản:* Điểm Coherence của B đạt **1.80/2.0**, trong khi A chỉ đạt **0.20/2.0**.
   - *Nguyên nhân kỹ thuật:* Chiến lược A cắt cố định 500 ký tự khiến các câu văn bị chặt đôi ở vị trí ngẫu nhiên (ví dụ cắt cụt giữa một mệnh đề tài chính phức tạp), làm đứt gãy mối liên hệ ngữ nghĩa trong không gian vector. Ngược lại, Chiến lược B tôn trọng ranh giới đoạn văn tự nhiên, giúp vector embedding thu được trọn vẹn ý đồ của tác giả.
2. **So sánh Chiến lược B (Toàn văn) và C (Có lọc Metadata):**
   - Trên các câu hỏi có chỉ định năm cụ thể (như `q03`, `q07`, `q10`, `q18`), Chiến lược C bảo đảm độ chính xác 100% không trả về bất kỳ chunk nào của năm khác. Điều này ngăn ngừa triệt để rủi ro hallucination khi LLM sinh câu trả lời dựa trên nhầm lẫn giữa số liệu tài chính năm 2023 và 2024.
3. **Phân tích 2 trường hợp truy vấn thất bại (Failure Cases):**
   - **Trường hợp 1 — Câu `q16` (Test, Báo cáo 2024):**
     - *Câu hỏi:* *"Who was President of the World Bank Group and Chairman of the Board of Executive Directors in 2024?"*
     - *Gold Target:* Trang 5 (Thư của Chủ tịch, chữ ký: *"Ajay Banga, President of the World Bank Group, Chairman of the Board of Executive Directors"*).
     - *Kết quả truy xuất:* Top-1 rơi vào Trang 11 (Điểm tương đồng: 0.3504, đoạn văn: *"The Board warmly welcomes his successor, Ajay Banga, as the 14th President of the World Bank Group..."*); Top-2 rơi vào Trang 93 (*"The Executive Directors select a President, who serves as Chair of the Board..."*).
     - *Phân tích nguyên nhân:* Về mặt ngữ nghĩa, chunk tại Trang 11 thực tế **đã trả lời chính xác** câu hỏi (Ajay Banga là Chủ tịch thứ 14 của WBG). Tuy nhiên, vì tiêu chí đánh giá benchmark định nghĩa gold page là trang 5 (thư ngỏ), hệ thống đánh dấu là Miss (không trúng gold page 5). Đây là hiện tượng *Label Divergence / Multi-grounding* điển hình trong bài toán RAG trên tài liệu lớn.
   - **Trường hợp 2 — Câu `q19` (Test, Báo cáo 2024):**
     - *Câu hỏi:* *"In the 2024 strategy numbers, what is the single overarching goal (1 GOAL) defined by the World Bank?"*
     - *Gold Target:* Trang 7 (Đoạn *"1 GOAL: To create more and better-paid jobs"*).
     - *Kết quả truy xuất:* Rank 1 rơi vào Trang 4 (score 0.4510), Rank 2 rơi vào Trang 18 (score 0.5030), Rank 3 rơi vào Trang 7 (score 0.5046). Tuy nhiên, chunk ở Rank 3 lại là đoạn *"10 Targets That set ambitious goals for 2030, 22 Scorecard indicators..."* chứ không chứa đoạn *"1 GOAL"*.
     - *Phân tích nguyên nhân:* Trang 7 của Báo cáo 2024 được thiết kế theo dạng Infographic 3 cột số liệu độc lập: `1 GOAL`, `10 Targets`, `22 Scorecard indicators`. Khi tách theo đoạn văn, trang này bị chia thành 3 chunk nhỏ. Chunk chứa cụm từ `goals for 2030` bị vectorizer gán độ tương đồng cao hơn do câu hỏi có chứa chữ "goal", làm lấn át chunk mục tiêu thực sự `1 GOAL`.

### Chiến lược chọn, đánh đổi, điều kiện áp dụng
- **Chiến lược được lựa chọn:** **Chiến lược C (Paragraph-aware Chunking kết hợp Metadata Filtering)**.
- **Lý do chọn:** Thỏa mãn toàn diện các tiêu chí đã đóng băng: Hit@3 trên Dev đạt **86.7%**, Coherence đạt **1.80/2.0**, và độ tuân thủ bộ lọc metadata đạt **100%**.
- **Đánh đổi (Trade-offs):**
  - Cần phải có metadata extractor hoặc query classifier phía trước để nhận diện xem câu hỏi của người dùng có chứa ràng buộc về năm (`year`) hay cơ quan (`institution`) hay không. Nếu người dùng hỏi câu hỏi chung không có năm, hệ thống phải tự động fallback về Chiến lược B.
  - Kích thước chunk theo đoạn văn không đều (biến thiên từ 150 đến 600 ký tự), khiến mật độ thông tin trong vector có thể chênh lệch.
- **Điều kiện áp dụng thực tế:** Phù hợp với các hệ thống RAG doanh nghiệp xử lý tài liệu hành chính, báo cáo tài chính hàng năm, hồ sơ pháp lý nơi mốc thời gian và thẩm quyền ban hành là yếu tố quyết định tính hợp lệ của câu trả lời.

### Hạn chế của dữ liệu, nhãn, test nhỏ, đo thời gian/chi phí
- **Tập Test nhỏ:** 5 câu hỏi trong tập Test có phương sai thống kê cao; chỉ cần trượt 1 câu là tỉ lệ giảm $20\%$. Điều này giải thích tại sao Hit@3 trên Test chỉ đạt 40% (2/5) trong khi Dev đạt 86.7% (13/15).
- **Hạn chế của Dense Retrieval thuần túy:** Mô hình embedding 384 chiều (`all-MiniLM-L6-v2`) có xu hướng trôi ngữ nghĩa (semantic drift) khi gặp các câu hỏi chứa số liệu chính xác (ví dụ câu `q09` hỏi về con số 70% phát thải, mô hình lại retrieve các đoạn nói chung về biến đổi khí hậu).
- **Đo thời gian:** Độ trễ truy vấn cực thấp ($0.04 - 0.06$s cho 20 câu hỏi) là do chạy local in-memory HNSW index trên tập 1.047 chunks. Khi mở rộng lên quy mô hàng triệu trang, độ trễ sẽ tăng và cần đo đạc lại trên cụm máy chủ chuyên dụng.

### Nếu làm lại hoặc mở rộng, cải tiến gì?
1. **Triển khai Tìm kiếm Lai (Hybrid Search: Dense + BM25):** Kết hợp vector embedding của MiniLM với bộ chỉ mục từ khóa BM25 qua thuật toán *Reciprocal Rank Fusion (RRF)*. Điều này sẽ khắc phục triệt để các ca thất bại như `q09` và `q19`, nơi các từ khóa đặc thù như `"70 percent"` hay `"1 GOAL"` bị vector dày đặc làm lu mờ.
2. **Tích hợp Re-ranker (Cross-Encoder / ColBERT):** Sau khi lấy Top-20 ứng viên từ bước Retrieval, sử dụng mô hình Cross-Encoder (như `bge-reranker-large` hoặc `ms-marco-MiniLM-L-6-v2`) để chấm điểm tương quan từng cặp (Query, Chunk). Việc này giúp đẩy đúng chunk có chứa evidence quote lên Rank 1.
3. **Chunking nhận biết cấu trúc (Structure-Aware / Markdown Chunking):** Thay vì chỉ dựa vào `\n\n`, sử dụng parser nhận diện heading cấp 1, cấp 2 và cấu trúc bảng biểu HTML/Markdown để giữ trọn vẹn ngữ cảnh của các trang Infographic tổng hợp số liệu.
4. **Mở rộng mô hình Embedding đa ngôn ngữ (Multilingual Embedding):** Sử dụng các mô hình như `text-embedding-3-small` hoặc `bge-m3` hỗ trợ vector 1024 chiều để nâng cao khả năng biểu diễn ngữ nghĩa cho cả tiếng Việt và tiếng Anh.
