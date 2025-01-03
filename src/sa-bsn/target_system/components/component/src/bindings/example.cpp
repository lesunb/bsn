#include <pybind11/pybind11.h>

namespace py = pybind11;

PYBIND11_MODULE(example, m)
{
    m.doc() = "Example Python module using Pybind11"; // Module docstring
    m.def("add", [](int a, int b)
          { return a + b; }, "A function that adds two numbers");
}
