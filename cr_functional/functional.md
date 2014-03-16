Domain: R^d, with d between 1 and 4 typically or a cartesian product of those.
Specified by an integer d or a tuple of integers.

TimeDomain may be a special domain.
  * t returns the current time (an abstract symbol)
  * operation on time: t+3 = time + 3 seconds
  * dt is a symbol representing a constant time step, 3*dt is an exact duration

Item belong to domain? x in Domain?

Function:
  
  * name (optional, None=anonymous function)
  * source domain, source dimension(s)
  * target domain, target dimension(s)
  * optional parameters
  * eval Python
  * eval vectorized NumPy
  * eval GLSL
  * possible inverse() method, returns a new function
  
Basic functions:

  * identity
  * projectors on a subspace
  * addition, subtraction, multiplication, division between two numbers
  * idem, but with a fixed number
  
Operations on functions:
  * composition with another function
  * +, -, *, /: composition with arithmetic functions
  * .x, .y, .r, .g, etc: projectors (GLSL conventions)
  * .first, .second, .third, .last: projectors on subspace of cartesian product
  
Standard mathematical functions:
  * exp, log, trigo, etc.

Higher-order functions:
  * composition
  * partial
  
Domains are checked for all operations.

Role of __call__:
  * if the argument matches the source domain: evaluate
  * on another function, if the domains match: compose
  * on an argument belonging to a strict cartesian subspace (e.g. (2, 3) for ExFxG): a partial function
  
Function with source TimeDomain:
  * when called without argument, returns the value for the current time
  * t represents the current time

### Examples

**Create a composite function**

```python
f = exp(3*x)+1  # x is a shortcut for the Identity function
```


**Implement a standard function**

```python
import math
import numpy as np
class exp(Function):
    def map(self, x):
        return math.exp(x)
    def map_vect(self, x):
        return np.exp(x)
    def map_glsl(self):
        return """
        // A full GLSL function will be automatically generated
        // with the appropriate signature and type declarations.
        y = exp(x);
        """
    def inverse(self):
        return log
```

**Higher-order function: derivative**

```python
@Functional()
def derivate(f):
    # t is a shortcut for now(): it represents the current time
    return (f(t) - f(t-dt)) / dt
```

**Higher-order function: linear filter**

```python
# Register a higher-order function (functional) with one real parameter
@Functional(tau=Real())
def filter(f):
    # Last value of the output (filtered) function.
    y = out(t-dt)
    # Last value of the input function.
    x = f(t-dt)
    return y + (-y + x) * dt / tau

# Smooth the mouse position.
f = filter(mouse_position, tau=1.)
    
```


