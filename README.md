# logicamente
A first-order logic theorem prover.

## Dependencies

- Python 3.7 (for `@dataclass` decorator)
- pyparsing 2.3.1

Available on pip, install with `pip install pyparsing`

## Running
Just

```
python3 main.py
```

The program asks for a Prolog-like knowledge base file and for a query.

There's an included example file called `underground`

Example usage:

```
$ python main.py

input file: ./underground

input query: reachable(tottenham_court_road,leicester_square, R)

backward_chain{ (reachable(tottenham_court_road, leicester_square, R)) }: True

result: (reachable(tottenham_court_road, leicester_square, (list())))
```

## Knowledge base quick start

- Variables: upper case + `_`

- Literals: lower case + `_`

- N-ary relations are supported, name same as literals

- `(A & B) => C` (implication) becomes `C :- A, B`

- Body of clause

- Lists: brackets, comma-separated `[a, B, foo(bar, Q)]`

- Every clause must end with `.`

- Clauses are resolved using the order provided in the KB file.
If there is a cycle it will be detected and can be corrected by changing the clauses' order.

- C-style comments supported

Example:

```
/* file: happy.pl */
smiles(P, Q) :- happy(P).
happy(P) :- loves(P, Q), rested(P).

rested(johnny).
loves(mary, johnny).

loves(P,Q) :- loves(Q,P).
```

```
$ python main.py
input file: happy.pl
input query: happy(X)
backward_chain{ (happy(X)) }: True
result: (happy(johnny))

```

---

Thanks to: https://stackoverflow.com/a/28398903 for Python implementation of Visitor pattern! :)
