from pkg.calculator import Calculator

calc = Calculator()
expression = '121 + 4343 * 23 + 56 / 8'
result = calc.evaluate(expression)
print(result)