# Step 2: Clifford Resynthesis


Task: Given a $CNOT$ + $T$ circuit $U$ and a Pauli string $P$. Resyntesise $C = U \, P \, U^\dagger$ s.t. $C$ has $0\,\, T$ gates.


Why is $C$ Clifford? We have that $C = P' \, Q$ where $P'$ is a Pauli string and $Q$ is a diagonal Clifford operator.

$U$ is a phase polynomial where all of the Rz gates have angles which are multiples of $\frac{\pi}{4}$.

$$
\begin{equation}
U = e^{2 \pi i p(x)}|Lx\rangle \langle x| = D \, L
\end{equation}
$$

$$
\begin{align}
C &= U\, P\, U^\dagger \\
  &= D\, L\, P\, L^\dagger D^\dagger \\
  &= D \, P'\, D^\dagger \\
  &= P' \, D' \, D^\dagger \\
C &= P' \, Q
\end{align}
$$

$$
D = \exp\Big( \frac{i}{2} \sum_j \theta_j\, S_j\Big)
$$

Lets consider $D$ to be a sequence of $\{Z, I\}$ Pauli strings $S_j$ and angles $\theta_j$ 



In our case $D$ is a diagonal $CNOT + T$ circuit so we have
$$
D: \Big\{\big(S_0, \,\frac{k_0\pi}{4}\big)\,, ...\,, \big(S_j, \,\frac{k_j \pi}{4}\big) \Big\}
$$ 
Here the $k_i$ terms are integers. Our circuit is non Clifford for $k$ values of $\pm 1$ which correspond to $T$ and $T^\dagger$ gates.

Given that all of the strings are tensor products of $Z$ and $I$ Paulis we know that these mutually commute with one another.

For $D^\dagger$ we just negate the angles. Note that $Z$ and $I$ are self-adjoint.

$$
D^\dagger: \Big\{\big(S_0, \,-\frac{k_0\pi}{4}\big)\,, ...\,, \big(S_j, \,-\frac{k_j \pi}{4}\big) \Big\}
$$ 

Now we obtain $D'$ from commuting the Pauli string $P'$ to the front of the circuit.

Lets define the indicator function $\eta(A, B)$.

$$
\eta(A, B) =\begin{cases}
0\,, \quad [A, \,B] = 0\\
1\,, \quad \text{otherwise}\\
\end{cases}
$$

So to construct $D'$ we negate the coefficients whenever the corresponding string does not commute with $P'$.

$$
D':  \Big\{\big(S_0, \,(-1)^{\eta(S_0, \, P')}\frac{k_0\pi}{4}\big)\,, \,...\,, \big(S_j, \,(-1)^{\eta(S_j, \, P')}\frac{k_j \pi}{4}\big) \Big\}
$$

Finally combining $D'$ with $D^\dagger$ to get $Q$ our Pauli strings will have the coefficients

$$
\theta_j = \frac{k_j \pi}{4}\Big( (-1)^{\eta(S_j, \,P')  } - 1\Big)
$$

$$
\theta_j 
= \begin{cases}
0\, \quad \quad \quad\text{if } [P',\,S_j] =0 \\
-  \frac{k_j\pi}{2}, \quad \text{if } [P',\,S_j] \neq 0
\end{cases}
$$


```python
from pytket.qasm import circuit_from_qasm
from pytket.circuit import PhasePolyBox
from topt_proto.clifford import synthesise_clifford
from topt_proto.utils import tensor_from_x_index

U_cnot_t_circuit = circuit_from_qasm("tests/qasm/cnot_t_4.qasm")
draw(U_cnot_t_circuit)
```


```python
ppbox_circ = PhasePolyBox(U_cnot_t_circuit)
pauli = tensor_from_x_index(1, n_qubits=3)
print(pauli)
```

```python
synthesise_clifford(ppbox_circ, input_pauli=pauli)
```