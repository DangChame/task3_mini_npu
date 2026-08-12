import json
import time


DATA_FILE = "data.json"
REPEAT = 10           # 성능 측정 반복 횟수
MANUAL_SIZE = 3       # 모드 1에서 입력받는 크기
PERF_SIZES = [3, 5, 13, 25]   # 성능 분석 대상 크기

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


class FlatMatrix:
    """n×n 배열을 1차원 리스트 하나에 펼쳐 담는다. (보너스: 메모리 접근 최적화)

    Matrix와 달리 data를 감추지 않고 그대로 노출한다. 이 클래스의 목적이
    접근 비용을 줄이는 것이라, 값을 꺼낼 때마다 메서드를 거치면 의미가 없다.
    (row, col) 좌표가 필요하면 data[row * size + col]로 찾는다.
    """

    def __init__(self, rows):
        self.size = len(rows)
        self.data = []
        for row in rows:
            for value in row:
                self.data.append(value)


def mac(pattern, filter_matrix):
    """MAC 연산: 같은 위치끼리 곱하고(Multiply) 전부 더한다(Accumulate)."""
    score = 0.0
    for row in range(pattern.size):
        for col in range(pattern.size):
            score += pattern.get(row, col) * filter_matrix.get(row, col)
    return score


def mac_flat(pattern, filter_matrix):
    """1차원 배열을 그대로 훑는 MAC. (보너스: 최적화 버전)"""
    score = 0.0
    for i in range(len(pattern.data)):
        score += pattern.data[i] * filter_matrix.data[i]
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


def make_empty(size):
    """전부 0.0으로 채운 size×size 행렬을 만든다."""
    rows = []
    for _ in range(size):
        # 행마다 새 리스트를 만들어야 한다. [[0.0] * size] * size로 쓰면
        # 같은 리스트를 size번 가리키게 되어 한 칸만 고쳐도 전부 바뀐다.
        rows.append([0.0] * size)
    return Matrix(rows)


def make_cross(size):
    """size×size 십자가(Cross) 패턴을 만든다. 가운데 행과 열이 1."""
    matrix = make_empty(size)
    mid = size // 2
    for i in range(size):
        matrix.set(mid, i, 1.0)   # 가운데 행 전체
        matrix.set(i, mid, 1.0)   # 가운데 열 전체
    return matrix


def make_x(size):
    """size×size X 패턴을 만든다. 두 대각선이 1."""
    matrix = make_empty(size)
    for i in range(size):
        matrix.set(i, i, 1.0)              # 왼쪽 위 → 오른쪽 아래
        matrix.set(i, size - 1 - i, 1.0)   # 오른쪽 위 → 왼쪽 아래
    return matrix


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


def ask_choice(title, options):
    """번호 메뉴를 보여주고 올바른 번호를 고를 때까지 다시 받는다."""
    while True:
        print(title)
        for number, text in enumerate(options, 1):
            print(f"{number}. {text}")
        answer = input("선택: ").strip()
        if answer.isdigit() and 1 <= int(answer) <= len(options):
            return int(answer)
        print(f"1~{len(options)} 사이 숫자를 입력하세요.\n")


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
            result.reason = (
                f"판정 {result.verdict} != expected {result.expected}"
            )
    return result


def analyze_patterns(data, filters):
    """모든 패턴 케이스를 판정해 결과 목록을 돌려준다."""
    results = []
    for key, case in data.get("patterns", {}).items():
        results.append(analyze_case(key, case, filters))
    return results


def measure_mac(pattern, filter_matrix, repeat=REPEAT, operation=mac):
    """MAC 연산만 repeat번 반복해 1회 평균 시간(ms)을 돌려준다."""
    start = time.perf_counter()
    for _ in range(repeat):
        operation(pattern, filter_matrix)
    elapsed = time.perf_counter() - start
    return elapsed / repeat * 1000


def print_performance(sizes, data=None):
    """크기별 MAC 평균 시간과 연산 횟수(N²)를 표로 출력한다.

    data는 (패턴, 필터) 짝이다. 주면 그 데이터로 재고(모드 1), 안 주면 크기마다
    생성기로 만들어 잰다(모드 2). MAC 시간은 값이 아니라 크기에만 좌우되므로
    어느 쪽이든 같은 크기면 결과는 같다.

    패턴과 필터를 따로 받지 않는 이유는 둘이 항상 짝으로 다녀야 하기 때문이다.
    매개변수를 둘로 나누면 한쪽만 넘기는 상태가 만들어지는데, 그러면 넘긴 값이
    조용히 무시되거나 None을 계산하려다 죽는다. 하나로 묶으면 그럴 수 없다.
    """
    if data is None:
        print("크기마다 생성기로 십자가(Cross) 패턴과 X 필터를 만들어 측정합니다.")
    else:
        print("위에서 준비한 패턴과 필터 A로 측정합니다.")
    print(f"{'크기':<10}{'평균 시간(ms)':<16}{'연산 횟수':<10}")
    print("-" * 38)
    for size in sizes:
        if data is None:
            target, other = make_cross(size), make_x(size)
        else:
            target, other = data
        average = measure_mac(target, other)
        print(
            f"{str(size) + '×' + str(size):<10}"
            f"{average:<16.3f}{size * size:<10}"
        )


def print_optimization(sizes):
    """2차원 방식과 1차원 방식의 MAC 성능을 비교해 표로 출력한다. (보너스)"""
    print(f"{'크기':<9}{'2차원(ms)':<13}{'1차원(ms)':<13}{'속도 향상':<11}{'결과 일치':<10}")
    print("-" * 56)
    for size in sizes:
        pattern = make_cross(size)
        filter_matrix = make_x(size)
        flat_pattern = FlatMatrix(pattern.rows)
        flat_filter = FlatMatrix(filter_matrix.rows)

        before = measure_mac(pattern, filter_matrix)
        after = measure_mac(flat_pattern, flat_filter, operation=mac_flat)

        score_before = mac(pattern, filter_matrix)
        score_after = mac_flat(flat_pattern, flat_filter)
        same = "O" if abs(score_before - score_after) < EPSILON else "X"

        speedup = before / after if after > 0 else 0.0
        label = str(size) + "×" + str(size)
        print(
            f"{label:<9}{before:<13.4f}{after:<13.4f}"
            f"{speedup:<11.2f}{same:<10}"
        )


def print_header(title):
    """구분선이 있는 섹션 제목을 출력한다."""
    print()
    print("#" + "-" * 40)
    print(f"# {title}")
    print("#" + "-" * 40)


def print_case(result):
    """케이스 하나의 판정 결과를 출력한다."""
    print(f"--- {result.name} ---")

    if result.cross_score is None:
        print(f"FAIL ({result.reason})")
        return

    print(f"Cross 점수: {result.cross_score}")
    print(f"X 점수: {result.x_score}")
    line = f"판정: {result.verdict} | expected: {result.expected} | "
    if result.passed:
        print(line + "PASS")
    else:
        print(line + f"FAIL ({result.reason})")


def print_summary(results):
    """전체 테스트 수, 통과/실패 수, 실패 케이스 목록을 출력한다."""
    total = len(results)
    passed = 0
    for result in results:
        if result.passed:
            passed += 1
    failed = total - passed

    print(f"총 테스트: {total}개")
    print(f"통과: {passed}개")
    print(f"실패: {failed}개")

    if failed > 0:
        print("실패 케이스:")
        for result in results:
            if not result.passed:
                print(f"  - {result.name}: {result.reason}")


def run_manual_mode():
    """모드 1: 3×3 필터 2개와 패턴을 직접 입력받아 판정한다."""
    print_header("[1] 필터 입력")
    source = ask_choice(
        "필터를 어떻게 준비할까요?",
        ["직접 입력", "자동 생성 (A=십자가, B=X)"],
    )
    if source == 2:
        filter_a = make_cross(MANUAL_SIZE)
        filter_b = make_x(MANUAL_SIZE)
        print(
            f"생성기로 {MANUAL_SIZE}×{MANUAL_SIZE} 십자가(Cross) 필터와 "
            "X 필터를 만들었습니다."
        )
    else:
        filter_a = ask_matrix("필터 A", MANUAL_SIZE)
        filter_b = ask_matrix("필터 B", MANUAL_SIZE)

    print("\n저장된 필터 A")
    filter_a.show()
    print("저장된 필터 B")
    filter_b.show()

    print_header("[2] 패턴 입력")
    pattern = ask_matrix("패턴", MANUAL_SIZE)
    print("\n저장된 패턴")
    pattern.show()

    print_header("[3] MAC 결과")
    score_a = mac(pattern, filter_a)
    score_b = mac(pattern, filter_b)
    average = measure_mac(pattern, filter_a)
    verdict = judge(score_a, score_b, "A", "B")

    print(f"A 점수: {score_a}")
    print(f"B 점수: {score_b}")
    print(f"연산 시간(평균/{REPEAT}회): {average:.3f} ms")
    if verdict == UNDECIDED:
        print(f"판정: 판정 불가 (|A-B| < {EPSILON})")
    else:
        print(f"판정: {verdict}")

    print_header("[4] 성능 분석")
    print_performance([MANUAL_SIZE], (pattern, filter_a))


def run_json_mode():
    """모드 2: data.json을 읽어 모든 케이스를 판정한다."""
    data = load_data(DATA_FILE)
    if data is None:
        return

    print_header("[1] 필터 로드")
    filters = load_filters(data)

    print_header("[2] 패턴 분석 (라벨 정규화 적용)")
    results = analyze_patterns(data, filters)
    for result in results:
        print_case(result)

    print_header(f"[3] 성능 분석 (평균/{REPEAT}회)")
    print_performance(PERF_SIZES)

    print_header("[4] 결과 요약")
    print_summary(results)


def show_menu():
    print()
    print("=== Mini NPU Simulator ===")
    print("[모드 선택]")
    print("1. 사용자 입력 (3x3)")
    print("2. data.json 분석")
    print("3. 최적화 비교 (보너스)")
    print("4. 종료")


def run():
    """메뉴를 반복하며 모드를 선택받는다."""
    try:
        while True:
            show_menu()
            choice = input("선택: ").strip()

            if choice == "1":
                run_manual_mode()
            elif choice == "2":
                run_json_mode()
            elif choice == "3":
                print_header(f"최적화 비교 (2차원 vs 1차원, 평균/{REPEAT}회)")
                print_optimization(PERF_SIZES)
            elif choice == "4":
                print("프로그램을 종료합니다.")
                break
            else:
                print("잘못된 입력입니다. 1~4 사이 숫자를 입력하세요.")
    except (KeyboardInterrupt, EOFError):
        print("\n입력이 중단되었습니다. 프로그램을 종료합니다.")


if __name__ == "__main__":
    run()
