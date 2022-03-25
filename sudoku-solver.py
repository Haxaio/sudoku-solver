from math import floor
import random
import time

from pyxel import rect, text
import pyxel


class Colors:
    def __init__(self):
        self.cell_outline = 5
        self.block_outline = 0
        self.text = 1
        self.cell = 6
        self.text_collapsed = 5
        self.cell_collapsed = 11
        self.text_lowest_entropy = 9
        self.cell_lowest_entropy = 10
        self.text_hover = 7
        self.probability_hover = 0
        self.text_disabled = 1
        self.cell_disabled = 12
        self.cell_error = 8


class Cell:
    def __init__(self, col, row):
        self.probabilities = [i for i in range(1, 10)]
        self.col = col
        self.row = row

    @property
    def collapsed(self):
        return self.entropy <= 1

    @property
    def state(self):
        if self.entropy > 0:
            return self.probabilities[0]
        return 0

    @property
    def entropy(self):
        return len(self.probabilities)


class SudokuBoard:
    def reset(self):
        self.cells = []
        for row_index in range(0, 9):
            row = []
            for col_index in range(0, 9):
                cell = Cell(col_index, row_index)
                row.append(cell)
            self.cells.append(row)

    def get_cell_neighbors(self, cell):
        row_cells = self.__get_row_cells(cell.row)
        col_cells = self.__get_col_cells(cell.col)
        block_cells = self.__get_block_cells(cell.col, cell.row)

        return row_cells + col_cells + block_cells

    # region Private Methods
    def __get_row_cells(self, row_index):
        return self.cells[row_index]

    def __get_col_cells(self, col_index):
        col = []
        for row in self.cells:
            col.append(row[col_index])
        return col

    def __get_block_cells(self, cell_col_index, cell_row_index):
        block_row_index = floor(cell_row_index / 3)
        ri_start = block_row_index * 3
        ri_end = ri_start + 3

        block_col_index = floor(cell_col_index / 3)
        ci_start = block_col_index * 3
        ci_end = ci_start + 3

        cells = []
        for ri in range(ri_start, ri_end):
            for ci in range(ci_start, ci_end):
                cells.append(self.cells[ri][ci])
        return cells

    # endregion


class SudokuSolver(SudokuBoard):
    def __init__(self):
        SudokuBoard.reset(self)

    def get_possible_states_for_cell(self, cell):
        possible_states = [i for i in range(1, 10)]

        for cell in self.get_cell_neighbors(cell):
            if cell.collapsed and cell.entropy > 0 and cell.state in possible_states:
                possible_states.remove(cell.state)

        return possible_states

    def get_most_likely_probability_for_cell(self, cell):
        if cell.entropy > 0:
            probabilities_weights = []

            neighbor_values = []
            for neighbor in self.get_cell_neighbors(cell):
                neighbor_values += neighbor.probabilities

            for probability in cell.probabilities:
                weight = neighbor_values.count(probability)
                probabilities_weights.append((weight, probability))

            probabilities_weights.sort()

            return probabilities_weights[0][1]

    def get_lowest_entropy_cell(self):
        uncollapsed_cells = [c for r in self.cells for c in r if not c.collapsed]
        uncollapsed_cells.sort(key=lambda cell: cell.entropy)

        if len(uncollapsed_cells) < 1:
            return None

        lowest_entropy = [c.entropy for c in uncollapsed_cells][0]
        lowest_entropy_cells = [
            c for c in uncollapsed_cells if c.entropy == lowest_entropy
        ]

        lowest_entropy_cell = lowest_entropy_cells[
            random.randrange(0, len(lowest_entropy_cells), 1)
        ]

        return lowest_entropy_cell

    def solve(self):
        self.lowest_entropy_cell = self.get_lowest_entropy_cell()
        while not self.collapsed():
            self.collapse_cell(self.lowest_entropy_cell)

    def collapse_cell(self, cell, state=None):
        if not state:
            state = self.get_most_likely_probability_for_cell(cell)

        cell.probabilities = [state]

        self.propagate()

    def propagate(self):
        for row_index, row in enumerate(self.cells):
            for col_index, cell in enumerate(row):
                cell = self.cells[row_index][col_index]
                if not cell.collapsed:
                    possible_states = self.get_possible_states_for_cell(cell)
                    cell.probabilities = possible_states
        self.lowest_entropy_cell = self.get_lowest_entropy_cell()

    def collapsed(self):
        for row in self.cells:
            for cell in row:
                if not cell.collapsed:
                    return False
        return True


class SudokuSolverGUI(SudokuSolver):
    def __init__(self):
        SudokuSolver.__init__(self)
        # Sizes
        self.character_size = 9
        self.cell_size = self.character_size * 3
        self.block_size = self.cell_size * 3
        self.screen_size = self.block_size * 3

        # Colors
        self.colors = Colors()

        # Controls
        self.debug = False
        self.help = False
        self.selected_value = None
        self.selected_cell = None
        self.selected_probability = None

        # Slow solve
        self.solving = False
        self.seconds_per_tick = 1
        self.last_tick = 0
        self.last_update = 0

        self.lowest_entropy_cell = self.get_lowest_entropy_cell()

        pyxel.init(self.screen_size, self.screen_size, title="Sudoku Solver")
        pyxel.mouse(True)
        pyxel.run(self.update, self.draw)

    def update(self):
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()
        if pyxel.btnp(pyxel.KEY_D):
            self.debug = not self.debug
        if pyxel.btnp(pyxel.KEY_H):
            self.help = not self.help
        if pyxel.btnp(pyxel.KEY_RETURN):
            self.solve()
        if pyxel.btnp(pyxel.KEY_S):
            self.solving = not self.solving
        if pyxel.btnp(pyxel.KEY_R):
            self.reset()
            self.lowest_entropy_cell = self.get_lowest_entropy_cell()
            self.selected_value = None
            self.selected_cell = None
            self.selected_probability = None

        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            self.handle_mouse_click(pyxel.mouse_x, pyxel.mouse_y)

        delta = time.time() - self.last_update
        self.last_tick += delta

        if self.solving and self.last_tick > self.seconds_per_tick:
            self.last_tick = 0
            if self.lowest_entropy_cell:
                self.collapse_cell(self.lowest_entropy_cell)

        self.last_update = time.time()

    def draw(self):
        # Clear background (color will appear as block gridlines)
        pyxel.cls(self.colors.block_outline)
        self.draw_grid()
        self.draw_probabilities()
        if self.debug:
            self.draw_debug()

    def draw_grid(self):
        # Draw blocks (color will appear as cell gridlines)
        size = self.block_size - 2
        for row_index in range(0, 3):
            for col_index in range(0, 3):
                x = col_index * self.block_size + 1
                y = row_index * self.block_size + 1
                pyxel.rect(x, y, size, size, self.colors.cell_outline)

        # Draw cells (color will appear as cell background)
        size = self.cell_size - 2
        for row_index in range(0, 9):
            for col_index in range(0, 9):
                x = col_index * self.cell_size + 1
                y = row_index * self.cell_size + 1
                color = self.colors.cell
                if (
                    self.selected_cell
                    and self.selected_cell.row == row_index
                    and self.selected_cell.col == col_index
                    or self.lowest_entropy_cell
                    and self.lowest_entropy_cell.row == row_index
                    and self.lowest_entropy_cell.col == col_index
                ):
                    color = self.colors.cell_lowest_entropy
                if self.cells[row_index][col_index].collapsed:
                    color = self.colors.cell_collapsed
                if (
                    self.cells[row_index][col_index].probabilities == [0]
                    or self.cells[row_index][col_index].probabilities == []
                ):
                    color = self.colors.cell_error
                pyxel.rect(x, y, size, size, color)

    def draw_probabilities(self):
        size = self.cell_size - 2

        for row in self.cells:
            for cell in row:
                cell_x = cell.col * self.cell_size + 1
                cell_y = cell.row * self.cell_size + 1
                for probability_index in range(0, 9):
                    probability_row = floor(probability_index / 3)
                    probability_col = probability_index % 3

                    px = cell_x + (probability_col * self.character_size) + 1
                    py = cell_y + (probability_row * self.character_size) + 1

                    probability = probability_index + 1

                    if probability in cell.probabilities:
                        pyxel.text(px, py, f"{probability}", self.colors.text)

    def draw_debug(self):
        if self.selected_cell:
            x = self.selected_cell.col * self.cell_size
            y = self.selected_cell.row * self.cell_size
            pyxel.rect(x, y, 10, 10, 0)
            pyxel.text(x, y, f"{x}:{y}", 15)
        if self.selected_probability:
            x = self.selected_probability[0] * self.character_size
            y = self.selected_probability[1] * self.character_size
            pyxel.rect(x, y, 10, 10, 0)
            pyxel.text(x, y, f"{x}:{y}", 15)
        if self.lowest_entropy_cell:
            x = self.lowest_entropy_cell.col * self.cell_size
            y = self.lowest_entropy_cell.row * self.cell_size
            pyxel.rect(x, y, 40, 40, 0)
            pyxel.text(x, y, f"{x}:{y}", 15)

    def handle_mouse_click(self, x, y):
        cell = self.cells[floor(y / 9 / 3)][floor(x / 9 / 3)]

        probability_col_index = floor(x / 9)
        probability_row_index = floor(y / 9)

        self.selected_value = (probability_col_index % 3 + 1) + 3 * (
            probability_row_index % 3
        )
        self.selected_cell = cell
        self.selected_probability = (probability_col_index, probability_row_index)

        possible_states = self.get_possible_states_for_cell(cell)

        if self.debug or self.selected_value in possible_states and not cell.collapsed:
            self.collapse_cell(cell, self.selected_value)


SudokuSolverGUI()
