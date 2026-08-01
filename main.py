import json


DATA_FILE = "data.json"

EPSILON = 1e-9        # 두 점수 차이가 이보다 작으면 동점으로 본다

CROSS = "Cross"       # 표준 라벨 (십자가)
X = "X"               # 표준 라벨 (X)
UNDECIDED = "UNDECIDED"   # 판정 불가 (동점)

# 파일에 적힌 표기 → 표준 라벨
LABEL_MAP = {
    "+": CROSS,
    "cross": CROSS,
    "x": X,
}


class Matrix:
    """n×n 2차원 배열(패턴 또는 필터)을 담는 데이터 구조."""

    def __init__(self, rows):
        self.rows = rows          # 2차원 리스트
        self.size = len(rows)     # n (행 개수)

    def get(self, row, col):
        return self.rows[row][col]

    def set(self, row, col, value):
        self.rows[row][col] = value

    def is_square(self):
        if self.size == 0:
            return False
        for row in self.rows:
            if len(row) != self.size:
                return False
        return True

    def show(self):
        for row in self.rows:
            print(" ".join(str(value) for value in row))


def mac(pattern, filter_matrix):
    """MAC 연산: 같은 위치끼리 곱하고(Multiply) 전부 더한다(Accumulate)."""
    score = 0.0
    for row in range(pattern.size):
        for col in range(pattern.size):
            score += pattern.get(row, col) * filter_matrix.get(row, col)
    return score


def normalize_label(raw):
    """파일에 적힌 라벨 표기를 표준 라벨(Cross/X)로 바꾼다. 모르는 값이면 None."""
    text = str(raw).strip().lower()
    return LABEL_MAP.get(text)


def judge(score_a, score_b, label_a, label_b):
    """두 점수를 비교해 이긴 쪽 라벨을 돌려준다. 차이가 EPSILON 미만이면 동점."""
    if abs(score_a - score_b) < EPSILON:
        return UNDECIDED
    if score_a > score_b:
        return label_a
    return label_b


def size_from_key(key):
    """'size_5' 또는 'size_5_1' 같은 키에서 크기 숫자를 뽑는다. 실패하면 None."""
    parts = key.split("_")
    if len(parts) < 2 or not parts[1].isdigit():
        return None
    return int(parts[1])


def load_data(path):
    """data.json을 읽어 딕셔너리로 돌려준다. 실패하면 None."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"오류: {path} 파일을 찾을 수 없습니다.")
    except json.JSONDecodeError:
        print(f"오류: {path} 내용이 올바른 JSON 형식이 아닙니다.")
    return None


def load_filters(data):
    """filters를 {크기: {표준라벨: Matrix}} 형태로 바꾼다."""
    filters = {}
    for size_key, group in data.get("filters", {}).items():
        size = size_from_key(size_key)
        if size is None:
            print(f"경고: 필터 키 '{size_key}' 형식을 알 수 없어 건너뜁니다.")
            continue

        table = {}
        for raw_label, rows in group.items():
            label = normalize_label(raw_label)
            if label is None:
                print(f"경고: 알 수 없는 필터 라벨 '{raw_label}' (건너뜀)")
                continue
            table[label] = Matrix(rows)

        filters[size] = table
        print(f"✓ size_{size} 필터 로드 완료 ({', '.join(sorted(table))})")
    return filters


class CaseResult:
    """패턴 케이스 하나의 판정 결과."""

    def __init__(self, name):
        self.name = name              # 케이스 이름 (예: size_5_1)
        self.cross_score = None       # Cross 필터 점수
        self.x_score = None           # X 필터 점수
        self.verdict = None           # 판정 (Cross / X / UNDECIDED)
        self.expected = None          # 정답 (정규화된 표준 라벨)
        self.passed = False           # PASS 여부
        self.reason = ""              # 실패 사유


def analyze_case(key, case, filters):
    """케이스 하나를 검증하고 판정한다. 문제가 있으면 그 케이스만 실패 처리한다."""
    result = CaseResult(key)

    size = size_from_key(key)
    if size is None:
        result.reason = "키에서 크기를 읽을 수 없음"
        return result

    if size not in filters:
        result.reason = f"size_{size} 필터가 없음"
        return result

    table = filters[size]
    if CROSS not in table or X not in table:
        result.reason = f"size_{size} 필터에 Cross/X가 모두 있지 않음"
        return result

    rows = case.get("input")
    if rows is None:
        result.reason = "input 항목이 없음"
        return result

    pattern = Matrix(rows)
    if not pattern.is_square():
        result.reason = "패턴이 정사각형이 아님"
        return result

    if pattern.size != size:
        result.reason = f"크기 불일치: 키는 {size}인데 실제 패턴은 {pattern.size}"
        return result

    result.expected = normalize_label(case.get("expected"))
    if result.expected is None:
        result.reason = f"알 수 없는 expected 값: {case.get('expected')}"
        return result

    result.cross_score = mac(pattern, table[CROSS])
    result.x_score = mac(pattern, table[X])
    result.verdict = judge(result.cross_score, result.x_score, CROSS, X)
    result.passed = result.verdict == result.expected

    if not result.passed:
        if result.verdict == UNDECIDED:
            result.reason = "동점(UNDECIDED) 처리 규칙에 따라 FAIL"
        else:
            result.reason = f"판정 {result.verdict} != expected {result.expected}"
    return result


def analyze_patterns(data, filters):
    """모든 패턴 케이스를 판정해 결과 목록을 돌려준다."""
    results = []
    for key, case in data.get("patterns", {}).items():
        results.append(analyze_case(key, case, filters))
    return results


def parse_row(line, size):
    """한 줄을 숫자 리스트로 바꾼다. 형식이 틀리면 None을 돌려준다."""
    values = line.split()
    if len(values) != size:
        print(f"입력 형식 오류: 각 줄에 {size}개의 숫자를 공백으로 구분해 입력하세요.")
        return None

    row = []
    for value in values:
        try:
            row.append(float(value))
        except ValueError:
            print(f"입력 형식 오류: '{value}'은(는) 숫자가 아닙니다.")
            return None
    return row


def ask_matrix(title, size):
    """size줄을 입력받아 Matrix로 만든다. 형식이 틀리면 처음부터 다시 받는다."""
    while True:
        print(f"{title} ({size}줄 입력, 공백 구분)")
        rows = []
        for _ in range(size):
            row = parse_row(input().strip(), size)
            if row is None:
                break
            rows.append(row)

        if len(rows) == size:
            return Matrix(rows)
        print("처음부터 다시 입력하세요.\n")
