#!/usr/bin/env python3

def fibonacci(n):
    """Return a list of the first n Fibonacci numbers."""
    if n <= 0:
        return []
    fib_seq = [0]
    if n == 1:
        return fib_seq
    fib_seq.append(1)
    for i in range(2, n):
        fib_seq.append(fib_seq[-1] + fib_seq[-2])
    return fib_seq


def main():
    seq = fibonacci(10)
    for num in seq:
        print(num)


if __name__ == "__main__":
    main()
