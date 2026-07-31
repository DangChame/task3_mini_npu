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
