from math import floor
import random
import time

import pyxel


class Cell:
    def __init__(self, col, row):
        self.collapsed = False
        self.probabilities = [i for i in range(1, 10)]
        self.col = col
        self.row = row

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

    def valid_numbers_for_cell(self, cell):
        valid_numbers = [i for i in range(1, 10)]

        row_cells = self.__get_row_cells(cell.row)
        col_cells = self.__get_col_cells(cell.col)
        block_cells = self.__get_block_cells(cell.col, cell.row)

        cells = row_cells + col_cells + block_cells

        for cell in cells:
            if (
                cell.collapsed
                and len(cell.probabilities) > 0
                and cell.probabilities[0] in valid_numbers
            ):
                valid_numbers.remove(cell.probabilities[0])

        return valid_numbers

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

    def solve(self):
        while not self.collapsed:
            self.lowest_entropy_cell = self.get_lowest_entropy_cell()
            if self.lowest_entropy_cell:
                self.collapse_cell(self.lowest_entropy_cell)

    def collapse_cell(self, cell, value=None):
        cell.collapsed = True
        if not value and len(cell.probabilities) > 0:
            value = cell.probabilities[random.randrange(0, len(cell.probabilities), 1)]

        if value:
            cell.probabilities = [value]

        self.propagate()

    def propagate(self):
        for row_index, row in enumerate(self.cells):
            for col_index, cell in enumerate(row):
                cell = self.cells[row_index][col_index]
                valid_numbers = self.valid_numbers_for_cell(cell)
                if not cell.collapsed:
                    cell.probabilities = valid_numbers

        self.lowest_entropy_cell = self.get_lowest_entropy_cell()
        if self.lowest_entropy_cell and self.lowest_entropy_cell.entropy == 1:
            self.collapse_cell(self.lowest_entropy_cell)

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

    @property
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
        self.background = 7
        self.background_dimmed = 8
        self.background_highlighted = 15
        self.foreground = 0
        self.foreground_dimmed = 1
        self.foreground_highlighted = 2
        self.block_outline = 5
        self.cell_outline = 6

        # Controls
        self.debug = False
        self.help = False
        self.selected_value = None
        self.selected_cell = None
        self.selected_probability = None

        # Slow solve
        self.solving = False
        self.seconds_per_tick = 0.25
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
        pyxel.cls(self.block_outline)
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
                pyxel.rect(x, y, size, size, self.cell_outline)

        # Draw cells (color will appear as cell background)
        size = self.cell_size - 2
        for row_index in range(0, 9):
            for col_index in range(0, 9):
                x = col_index * self.cell_size + 1
                y = row_index * self.cell_size + 1
                color = self.background
                if (
                    self.selected_cell
                    and self.selected_cell.row == row_index
                    and self.selected_cell.col == col_index
                    or self.lowest_entropy_cell
                    and self.lowest_entropy_cell.row == row_index
                    and self.lowest_entropy_cell.col == col_index
                ):
                    color = self.background_highlighted
                if self.cells[row_index][col_index].collapsed:
                    color = self.background_dimmed
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
                        pyxel.text(px, py, f"{probability}", self.foreground)

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

        valid_numbers = self.valid_numbers_for_cell(cell)

        if self.debug or self.selected_value in valid_numbers and not cell.collapsed:
            self.collapse_cell(cell, self.selected_value)


SudokuSolverGUI()
