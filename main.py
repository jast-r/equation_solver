from operator import contains
import os
from typing import Any, List, Union
from fastapi import FastAPI
from pydantic import BaseModel, Field
import sympy

app = FastAPI(
    title="Equations",
    description="Сервис по решению уравнений, примеров и логических выражений.",
    version="0.0.1",
)


class Equations(BaseModel):
    equations: List[str]

    class Config:
        schema_extra = {
            "example": {
                "equations": [
                    "1x+3+2x+4x+5x=7x",
                    "3+5",
                    "2784=3738",
                    "1+2:3*4-(-(5^6)+7)*8+9=2:3*4-(-(5^6)+7)*8+9x",
                    "3,4+2,5",
                    "2784=3738",
                ]
            }
        }


class Response(BaseModel):
    source: str = Field(..., description="Исходное уравнение.")
    solve: Union[str, int, Any] = Field(
        ..., description="Решение уравнения в терминах языка программирования.")
    latex: str = Field(
        default="", description="Интерпретация решения в форме Latex.")


@app.post("/api/solve",
          response_model=List[Response],
          description=("Данный метод принимает список строк, которые являются неким математическим выражением. Пример: `1x+3+2x+4x+5x=7x`.\n\n"
                       u"В solve находится решение в виде терминов языка программирования. То есть, решением выражения `x\u00b2=5` будет: `sqrt(5), -sqrt(5)`.\n\n"
                       "Для решения данной проблемы (если она существует) можно парсить поле Latex.\n\n"
                       "Решение одного уравнения занимает около 25 миллисекунд (для уравнения двух переменных). Исходя из этого необходимо рассчитывать количество строк, передаваемых в запросе."),
          tags=["Solver"])
async def equation_solver(req: Equations):
    solve_list = list()
    for equation in req.equations:
        equation = scientify_equation(equation=equation)

        if equation.find('=') >= 0:
            res = handler_with_equal_sign(equation=equation)
            str_repr = repr(res).replace('[', '').replace(']', '')
            latex_repr = sympy.latex(res).replace('[', '').replace(']', '')
            resp = Response(source=equation,
                            solve=str_repr,
                            latex=latex_repr)
            solve_list.append(resp)
            continue

        if equation.find('x') >= 0 or equation.find('y') >= 0:
            equation += '=0'
            res = handler_with_equal_sign(equation=equation)
            str_repr = repr(res).replace('[', '').replace(']', '')
            latex_repr = sympy.latex(res).replace('[', '').replace(']', '')
            resp = Response(source=equation,
                            solve=str_repr,
                            latex=latex_repr)
            solve_list.append(resp)
            continue

    return solve_list


def find_all_char_pos(s: str, c: str):
    return [i for i, v in enumerate(s) if v == c]


def scientify_equation(equation: str) -> str:
    equation = equation.replace(' ', '')
    equation = equation.replace('^', '**')
    equation = equation.replace(':', '/')

    x_idx = find_all_char_pos(equation, 'x')
    y_idx = find_all_char_pos(equation, 'y')

    replace_counter = 0
    for pos in x_idx:
        if pos > 0:
            if equation[pos + replace_counter - 1].isdigit():
                equation = equation[:pos + replace_counter] + \
                    '*' + equation[pos+replace_counter:]
                replace_counter += 1

    replace_counter = 0
    for pos in y_idx:
        if pos > 0:
            if equation[pos + replace_counter - 1].isdigit():
                equation = equation[:pos + replace_counter] + \
                    '*' + equation[pos+replace_counter:]
                replace_counter += 1

    return equation


def handler_with_equal_sign(equation: str):
    eq_parts = equation.split('=')
    if len(eq_parts) != 2:
        sp_eq = equation
        if len(eq_parts == 1):
            eq_parts[1] = 0
        else:
            return

    sp_eq = sympy.Eq(*map(sympy.sympify, eq_parts))

    x_flag = False
    y_flag = False

    if equation.find('x') >= 0:
        x_flag = True
    if equation.find('y') >= 0:
        y_flag = True

    if x_flag and y_flag:
        return two_var_handler(eq=sp_eq)
    elif x_flag or y_flag:
        return one_var_handler(eq=sp_eq)

    solve = sympy.sympify(sp_eq)

    return solve


def one_var_handler(eq: Any):
    solve = sympy.solve(sympy.sympify(eq))

    return solve


def two_var_handler(eq: Any):
    solve = sympy.solve(sympy.sympify(eq), 'y')

    return solve


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, port=int(os.environ["APP_PORT"]), host="0.0.0.0")
