# Sample data for initializing the database

SAMPLE_QUESTIONS = [
    {"text_ar": "أستمتع بإصلاح أو تركيب الأشياء الميكانيكية", "axis": "R"},
    {"text_ar": "أفضل العمل العملي باستخدام الأدوات", "axis": "R"},
    {"text_ar": "أحب العمل في الورش والمختبرات", "axis": "R"},
    {"text_ar": "أستمتع بالأعمال اليدوية والحرفية", "axis": "R"},
    {"text_ar": "أفضل العمل في البيئة الخارجية", "axis": "R"},
    {"text_ar": "أستمتع بحل المسائل المعقدة والمنطقية", "axis": "I"},
    {"text_ar": "أحب إجراء التجارب العلمية", "axis": "I"},
    {"text_ar": "أستمتع بتحليل البيانات والمعلومات", "axis": "I"},
    {"text_ar": "أحب البحث والدراسة المتعمقة", "axis": "I"},
    {"text_ar": "أستمتع بفهم كيفية عمل الأشياء", "axis": "I"},
    {"text_ar": "أحب الرسم والتصميم الفني", "axis": "A"},
    {"text_ar": "أستمتع بالكتابة الإبداعية", "axis": "A"},
    {"text_ar": "أحب الموسيقى والفنون الأدائية", "axis": "A"},
    {"text_ar": "أستمتع بابتكار أفكار جديدة وأصيلة", "axis": "A"},
    {"text_ar": "أحب التعبير عن نفسي بطرق إبداعية", "axis": "A"},
    {"text_ar": "أستمد طاقتي من مساعدة الآخرين", "axis": "S"},
    {"text_ar": "أحب التدريس والإرشاد", "axis": "S"},
    {"text_ar": "أستمتع بالعمل مع الأطفال", "axis": "S"},
    {"text_ar": "أحب المشاركة في الأعمال التطوعية", "axis": "S"},
    {"text_ar": "أستمتع بحل مشاكل الناس", "axis": "S"},
    {"text_ar": "أحب قيادة الفرق واتخاذ القرارات", "axis": "E"},
    {"text_ar": "أستمتع بالتفاوض والإقناع", "axis": "E"},
    {"text_ar": "أحب تنظيم الفعاليات والمشاريع", "axis": "E"},
    {"text_ar": "أستمتع بإدارة الأعمال", "axis": "E"},
    {"text_ar": "أحب المخاطرة المحسوبة في العمل", "axis": "E"},
    {"text_ar": "أفضل الأعمال المنظمة والروتينية", "axis": "C"},
    {"text_ar": "أستمتع بترتيب البيانات والجداول", "axis": "C"},
    {"text_ar": "أحب العمل بالأرقام والحسابات", "axis": "C"},
    {"text_ar": "أستمتع بالأعمال المكتبية والإدارية", "axis": "C"},
    {"text_ar": "أحب اتباع القواعد والإجراءات", "axis": "C"}
]

SAMPLE_INSTITUTIONS = [
    {"name_ar": "جامعة بغداد", "city": "بغداد", "governorate": "بغداد", "type": "university"},
    {"name_ar": "جامعة البصرة", "city": "البصرة", "governorate": "البصرة", "type": "university"},
    {"name_ar": "جامعة الموصل", "city": "الموصل", "governorate": "نينوى", "type": "university"},
    {"name_ar": "الجامعة التكنولوجية", "city": "بغداد", "governorate": "بغداد", "type": "university"},
    {"name_ar": "معهد التدريب النفطي", "city": "كركوك", "governorate": "كركوك", "type": "institute"}
]

SAMPLE_MAJORS = [
    {"college_name_ar": "كلية الهندسة", "major_name_ar": "هندسة ميكانيكية", "branch_eligibility": ["scientific"], "study_mode": "morning", "riasec_match": ["R", "I"]},
    {"college_name_ar": "كلية الهندسة", "major_name_ar": "هندسة مدنية", "branch_eligibility": ["scientific"], "study_mode": "both", "riasec_match": ["R", "I"]},
    {"college_name_ar": "كلية الطب", "major_name_ar": "الطب العام", "branch_eligibility": ["scientific"], "study_mode": "morning", "riasec_match": ["I", "S"]},
    {"college_name_ar": "كلية الصيدلة", "major_name_ar": "الصيدلة", "branch_eligibility": ["scientific"], "study_mode": "morning", "riasec_match": ["I", "S"]},
    {"college_name_ar": "كلية علوم الحاسوب", "major_name_ar": "علوم الحاسوب", "branch_eligibility": ["scientific"], "study_mode": "both", "riasec_match": ["I", "C"]},
    {"college_name_ar": "كلية الفنون الجميلة", "major_name_ar": "التصميم", "branch_eligibility": ["arts", "literary"], "study_mode": "morning", "riasec_match": ["A"]},
    {"college_name_ar": "كلية التربية", "major_name_ar": "التربية", "branch_eligibility": ["scientific", "literary"], "study_mode": "both", "riasec_match": ["S"]},
    {"college_name_ar": "كلية الإدارة والاقتصاد", "major_name_ar": "إدارة الأعمال", "branch_eligibility": ["scientific", "literary"], "study_mode": "both", "riasec_match": ["E", "C"]},
    {"college_name_ar": "كلية الإدارة والاقتصاد", "major_name_ar": "المحاسبة", "branch_eligibility": ["scientific", "literary"], "study_mode": "both", "riasec_match": ["C"]},
    {"college_name_ar": "كلية الآداب", "major_name_ar": "اللغة العربية", "branch_eligibility": ["literary"], "study_mode": "both", "riasec_match": ["A", "S"]},
    {"college_name_ar": "كلية الإعلام", "major_name_ar": "الصحافة", "branch_eligibility": ["literary"], "study_mode": "morning", "riasec_match": ["A", "E"]},
    {"college_name_ar": "كلية التمريض", "major_name_ar": "التمريض", "branch_eligibility": ["scientific"], "study_mode": "morning", "riasec_match": ["S", "I"]}
]