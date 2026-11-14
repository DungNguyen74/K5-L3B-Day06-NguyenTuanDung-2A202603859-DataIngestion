"""Build and verify benchmark/questions.json for Day 06.
Ensures:
- Exactly 20 questions (15 dev, 5 test)
- 4 questions with metadata filter (3 in dev, 1 in test)
- All 4 question types: truc_tiep, dien_dat_lai, dieu_kien_ngoai_le, loc_metadata
- 100% of evidence_quotes verified to exist verbatim in normalized page text.
"""
import json
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parents[2]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from starter.src.ingestion import load_pdf

p24, _ = load_pdf(root_dir / 'data' / 'world_bank_annual_report_2024.pdf', 'wb_annual_report_2024', 'data/world_bank_annual_report_2024.pdf', {'year': 2024})
p23, _ = load_pdf(root_dir / 'data' / 'world_bank_annual_report_2023.pdf', 'wb_annual_report_2023', 'data/world_bank_annual_report_2023.pdf', {'year': 2023})

pages_by_doc = {
    'wb_annual_report_2024': {p.page: p.text for p in p24},
    'wb_annual_report_2023': {p.page: p.text for p in p23}
}

raw_questions = [
    # ----------------- DEV SET (15 questions: q01 - q15) -----------------
    {
        "id": "q01",
        "split": "dev",
        "type": "truc_tiep",
        "question": "Nền tảng bảo lãnh của Nhóm Ngân hàng Thế giới (Guarantee Platform) được đặt tại cơ quan nào?",
        "expected_answer": "Được đặt tại MIGA (Multilateral Investment Guarantee Agency).",
        "gold_source_id": "wb_annual_report_2024",
        "gold_page": 4,
        "evidence_quote": "The World Bank Group Guarantee Platform, \nhosted at MIGA, continues to play a vital role in \nbringing private capital to emerging markets.",
        "filter": None
    },
    {
        "id": "q02",
        "split": "dev",
        "type": "truc_tiep",
        "question": "Thiệt hại tái thiết ước tính đối với cơ sở hạ tầng năng lượng của Ukraine được nêu trong báo cáo năm 2024 là bao nhiêu?",
        "expected_answer": "Ước tính khoảng 91 tỷ USD (91 billion).",
        "gold_source_id": "wb_annual_report_2024",
        "gold_page": 10,
        "evidence_quote": "Attacks to Ukraine’s energy infrastructure have created an estimated $91 billion \nin reconstruction needs.",
        "filter": None
    },
    {
        "id": "q03",
        "split": "dev",
        "type": "truc_tiep",
        "question": "Các trang trại gia đình ở Brazil tạo việc làm cho bao nhiêu người theo báo cáo năm 2024?",
        "expected_answer": "Gần 10 triệu người (nearly 10 million people).",
        "gold_source_id": "wb_annual_report_2024",
        "gold_page": 11,
        "evidence_quote": "Brazil’s family farms employ nearly 10 million people and play a central \nrole in food production.",
        "filter": None
    },
    {
        "id": "q04",
        "split": "dev",
        "type": "truc_tiep",
        "question": "Ngành du lịch đóng góp bao nhiêu phần trong GDP của Cabo Verde?",
        "expected_answer": "Chiếm hơn một phần tư GDP (over a quarter of GDP).",
        "gold_source_id": "wb_annual_report_2024",
        "gold_page": 13,
        "evidence_quote": "Tourism is an engine of Cabo Verde’s economy, accounting for over a \nquarter of GDP.",
        "filter": None
    },
    {
        "id": "q05",
        "split": "dev",
        "type": "truc_tiep",
        "question": "Chương trình Hydrogen xanh quốc gia của Ấn Độ hướng tới mục tiêu tạo ra bao nhiêu việc làm?",
        "expected_answer": "Mục tiêu thúc đẩy tạo ra 600.000 việc làm (600,000 jobs).",
        "gold_source_id": "wb_annual_report_2024",
        "gold_page": 14,
        "evidence_quote": "Its National Green Hydrogen Mission, which aims to catalyze \n600,000 jobs",
        "filter": None
    },
    {
        "id": "q06",
        "split": "dev",
        "type": "dien_dat_lai",
        "question": "Theo báo cáo năm 2024, vấn đề an ninh nguồn nước tại Jordan có tầm quan trọng như thế nào đối với sự phát triển kinh tế?",
        "expected_answer": "An ninh nguồn nước là nền tảng cho năng suất và tăng trưởng kinh tế, đặc biệt khi Jordan là một trong những quốc gia khan hiếm nước nhất thế giới.",
        "gold_source_id": "wb_annual_report_2024",
        "gold_page": 9,
        "evidence_quote": "Water security is foundational for productivity and economic growth. As one \nof the most water-scarce countries in the world, Jordan has struggled to",
        "filter": None
    },
    {
        "id": "q07",
        "split": "dev",
        "type": "dien_dat_lai",
        "question": "Các quốc đảo Thái Bình Dương đang phải đối mặt với nguy cơ bệnh tật nghiêm trọng nào?",
        "expected_answer": "Tỷ lệ tử vong sớm và khuyết tật cao hàng đầu thế giới do các bệnh không lây nhiễm (non-communicable disease) như tiểu đường.",
        "gold_source_id": "wb_annual_report_2024",
        "gold_page": 12,
        "evidence_quote": "Pacific Island countries face some of the world’s highest rates of premature death and \ndisability from non-communicable disease, including diabetes,",
        "filter": None
    },
    {
        "id": "q08",
        "split": "dev",
        "type": "dien_dat_lai",
        "question": "Tại Indonesia, hơn 40% lượng phát thải khí nhà kính của quốc gia này xuất phát từ đâu?",
        "expected_answer": "Xuất phát từ nạn phá rừng và các vụ cháy giải phóng carbon vào khí quyển (deforestation and fires).",
        "gold_source_id": "wb_annual_report_2023",
        "gold_page": 31,
        "evidence_quote": "In Indonesia, more than 40 percent of the country’s emissions result from defor -\nestation and fires that release carbon into the atmosphere.",
        "filter": None
    },
    {
        "id": "q09",
        "split": "dev",
        "type": "dieu_kien_ngoai_le",
        "question": "Theo báo cáo năm 2023, các chiến lược phát triển phát thải carbon thấp có thể giúp giảm bao nhiêu phần trăm khí thải mà không gây hại cho tăng trưởng?",
        "expected_answer": "Có thể giảm phát thải 70% mà không gây hại cho tăng trưởng (without harming growth).",
        "gold_source_id": "wb_annual_report_2023",
        "gold_page": 14,
        "evidence_quote": "Collectively, the low-carbon development strategies from these reports can reduce \nemissions by 70 percent, without harming growth.",
        "filter": None
    },
    {
        "id": "q10",
        "split": "dev",
        "type": "dieu_kien_ngoai_le",
        "question": "Thiệt hại do cơn bão Freddy gây ra tại Malawi được mô tả như thế nào trong báo cáo 2023?",
        "expected_answer": "Hơn 1.000 sinh mạng thiệt mạng, hàng trăm nghìn người phải di dời, đường sá, cầu cống, bệnh viện và đường dây điện bị phá hủy.",
        "gold_source_id": "wb_annual_report_2023",
        "gold_page": 23,
        "evidence_quote": "With over 1,000 lives lost, hundreds of thousands displaced in camps, and roads, \nbridges, schools, hospitals, and powerlines damaged, Cyclone Freddy",
        "filter": None
    },
    {
        "id": "q11",
        "split": "dev",
        "type": "dieu_kien_ngoai_le",
        "question": "Vai trò của Ngân hàng Thế giới đối với các Quỹ trung gian tài chính (FIFs) trong báo cáo 2024 là gì?",
        "expected_answer": "Ngân hàng Thế giới cung cấp hỗ trợ hành chính (provides administrative support).",
        "gold_source_id": "wb_annual_report_2024",
        "gold_page": 26,
        "evidence_quote": "Financial intermediary funds (FIFs) represent large, \ndistinct, multi-partner financing arrangements, for \nwhich the World Bank provides administrative support.",
        "filter": None
    },
    {
        "id": "q12",
        "split": "dev",
        "type": "loc_metadata",
        "question": "Trong năm tài chính 2024, Ngân hàng Thế giới nêu rõ các trụ cột nào trong chiến lược việc làm?",
        "expected_answer": "3 trụ cột: Đầu tư vào hạ tầng vật chất và con người; Hỗ trợ môi trường kinh doanh với quy định rõ ràng; Huy động vốn tư nhân ở quy mô lớn.",
        "gold_source_id": "wb_annual_report_2024",
        "gold_page": 7,
        "evidence_quote": "3 Pillars\nInvest in foundational physical \nand human infrastructure\nSupport a business-enabling \nenvironment with clear rules \nand regulations\nMobilize private capital \nat scale",
        "filter": {"year": 2024}
    },
    {
        "id": "q13",
        "split": "dev",
        "type": "loc_metadata",
        "question": "Cột mốc bảo lãnh tích lũy mà MIGA đã đạt được kể từ khi thành lập năm 1988 theo báo cáo 2024 là bao nhiêu?",
        "expected_answer": "MIGA đã vượt qua mốc 100 tỷ USD phát hành bảo lãnh tích lũy.",
        "gold_source_id": "wb_annual_report_2024",
        "gold_page": 4,
        "evidence_quote": "The Board commends MIGA for surpassing \n$100 billion in cumulative guarantee issuance \nsince its founding in 1988",
        "filter": {"year": 2024}
    },
    {
        "id": "q14",
        "split": "dev",
        "type": "loc_metadata",
        "question": "Theo báo cáo năm 2023, bình đẳng giới tại Tây và Trung Phi đóng vai trò gì ngoài việc xây dựng xã hội hòa nhập?",
        "expected_answer": "Thúc đẩy tiến trình phát triển trong các lĩnh vực khác, từ cải thiện vốn con người và an ninh lương thực đến ứng phó biến đổi khí hậu.",
        "gold_source_id": "wb_annual_report_2023",
        "gold_page": 27,
        "evidence_quote": "Gender equality is not only essential for building more inclusive societies, but it \ncan also accelerate progress in other areas of development, from improving human \ncapital and food security to addressing climate change",
        "filter": {"year": 2023}
    },
    {
        "id": "q15",
        "split": "dev",
        "type": "dien_dat_lai",
        "question": "Những thách thức gắn kết chặt chẽ nào đang làm xói mòn thành quả phát triển theo thông điệp Chủ tịch năm 2023?",
        "expected_answer": "Nghèo đói, đại dịch, biến đổi khí hậu, nợ nần, xung đột, mất an ninh lương thực và tình trạng dễ bị tổn thương.",
        "gold_source_id": "wb_annual_report_2023",
        "gold_page": 9,
        "evidence_quote": "poverty, pandem-\nics, climate change, debt, \nconflict, food insecurity, and \nfragility—are eroding decades of hard-\nwon development progress",
        "filter": None
    },

    # ----------------- TEST SET (5 questions: q16 - q20) -----------------
    {
        "id": "q16",
        "split": "test",
        "type": "truc_tiep",
        "question": "Ai là Chủ tịch Nhóm Ngân hàng Thế giới kiêm Chủ tịch Ban Giám đốc Điều hành được ghi nhận trong báo cáo năm 2024?",
        "expected_answer": "Ajay Banga.",
        "gold_source_id": "wb_annual_report_2024",
        "gold_page": 5,
        "evidence_quote": "Ajay Banga\nPresident of the World Bank Group \nChairman of the Board of Executive Directors",
        "filter": None
    },
    {
        "id": "q17",
        "split": "test",
        "type": "dien_dat_lai",
        "question": "Theo báo cáo năm 2024, Ngân hàng Thế giới hợp tác với những đối tượng nào trong hệ sinh thái đối tác xã hội dân sự?",
        "expected_answer": "Hợp tác với xã hội dân sự, tổ chức tôn giáo, khu vực tư nhân, các quỹ, viện nghiên cứu, giới học thuật, cựu sinh viên và thanh niên.",
        "gold_source_id": "wb_annual_report_2024",
        "gold_page": 21,
        "evidence_quote": "The World Bank Group engages with a vibrant \necosystem of partners including civil society, faith-\nbased organizations, the private sector, foundations, \nthink tanks, academia, alumni, and youth.",
        "filter": None
    },
    {
        "id": "q18",
        "split": "test",
        "type": "dieu_kien_ngoai_le",
        "question": "Những cuộc khủng hoảng nào đồng thời hội tụ được báo cáo năm 2023 nhấn mạnh như một kỷ nguyên mới trong phát triển?",
        "expected_answer": "Biến đổi khí hậu, lạm phát, xung đột và mất an ninh lương thực, trong đó các nước đang phát triển bị ảnh hưởng nặng nề nhất.",
        "gold_source_id": "wb_annual_report_2023",
        "gold_page": 7,
        "evidence_quote": "world is facing an unprecedented confluence of crises—including \nclimate change, inflation, conflict, and food insecurity—with develop-\ning countries hardest hit.",
        "filter": None
    },
    {
        "id": "q19",
        "split": "test",
        "type": "loc_metadata",
        "question": "Theo báo cáo năm 2024, mục tiêu trọng tâm (1 GOAL) được đặt ra là gì?",
        "expected_answer": "Tạo ra nhiều việc làm hơn và được trả lương tốt hơn (To create more and better-paid jobs).",
        "gold_source_id": "wb_annual_report_2024",
        "gold_page": 7,
        "evidence_quote": "1 GOAL\nTo create more and \nbetter-paid jobs",
        "filter": {"year": 2024}
    },
    {
        "id": "q20",
        "split": "test",
        "type": "truc_tiep",
        "question": "Trong báo cáo năm 2023, Ban Giám đốc Điều hành khẳng định hành động vì khí hậu có vị thế gì trong các ưu tiên toàn cầu?",
        "expected_answer": "Hành động vì khí hậu tiếp tục là ưu tiên sống còn trên quy mô toàn cầu (crucial global priority).",
        "gold_source_id": "wb_annual_report_2023",
        "gold_page": 11,
        "evidence_quote": "Climate action remains a crucial global priority. The Executive Directors wel - \ncome the efforts the Bank Group",
        "filter": None
    }
]

print("=== VERIFYING EVIDENCE QUOTES AGAINST SOURCE TEXT ===")
verified_questions = []
all_valid = True

def clean(s):
    import re
    # Remove line-break hyphenation
    s = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', s)
    # Normalize em-dash and en-dash to regular dash
    s = s.replace('—', '-').replace('–', '-')
    # Normalize whitespace
    return re.sub(r'\s+', ' ', s.lower().replace('\n', ' ')).strip()

for q in raw_questions:
    doc_id = q["gold_source_id"]
    page_num = q["gold_page"]
    quote = q["evidence_quote"]
    
    page_text = pages_by_doc.get(doc_id, {}).get(page_num, "")
    
    if clean(quote) not in clean(page_text):
        print(f"FAILED on question {q['id']}: Quote not found on page {page_num} of {doc_id}!")
        print("Expected:", repr(quote))
        print("Page text sample:", repr(page_text[:300]))
        all_valid = False
    else:
        verified_questions.append(q)

if all_valid and len(verified_questions) == 20:
    benchmark_dir = root_dir / 'benchmark'
    benchmark_dir.mkdir(exist_ok=True)
    out_file = benchmark_dir / 'questions.json'
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(verified_questions, f, ensure_ascii=False, indent=2)
    print(f"\nALL 20 QUESTIONS VERIFIED! Benchmark successfully written to {out_file}")
    
    dev_count = sum(1 for q in verified_questions if q['split'] == 'dev')
    test_count = sum(1 for q in verified_questions if q['split'] == 'test')
    filter_count = sum(1 for q in verified_questions if q['filter'] is not None)
    test_filter_count = sum(1 for q in verified_questions if q['split'] == 'test' and q['filter'] is not None)
    print(f"Summary: {dev_count} dev, {test_count} test, {filter_count} total filter ({test_filter_count} in test).")
else:
    sys.exit("Verification failed!")
