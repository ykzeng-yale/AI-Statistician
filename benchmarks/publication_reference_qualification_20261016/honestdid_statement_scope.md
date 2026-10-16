# HonestDiD Statement-Scope Check

2026-10-16. Evaluator-side, operator-derived mathematical finding. Not a generated
research result, external referee endorsement, Lean proof, complete paper audit
or a newly activated gold rubric. Keep this file outside author source capsules.

## Exact Claim And Scope

The [journal-format main paper](https://www.jonathandroth.com/assets/files/HonestParallelTrends_Main.pdf),
printed page 2562 / PDF page 8, Lemma 2.1 and equations (4)--(6), was checked in
the original rendered page. PDF SHA-256:
`2ef3448e51bb946478ad323b8e00fc5de80fcc1b274ec26aa01dfaa9e458b7dc`.
Its convexity argument does establish that the nonempty scalar identified set
is an interval. Closedness of the restriction set alone does not ensure that
this interval is closed or that the displayed linear extrema are attained.

The following counterexample addresses that literal generality only. It does
not refute the paper's later polyhedral procedures, their coverage results or
its numerical findings. Full argument adjudication remains open.

## Counterexample

Use one pre-treatment coordinate and two post-treatment coordinates. Set
$\beta=(0,0,0)'$ and $l=(1,0)'$. Write
$\delta=(a,x,y)'$, with $a=\delta_{pre}$ and
$(x,y)'=\delta_{post}$. Define

$$
\Delta=\{(a,x,y)'\in\mathbb R^3:
 a=0,\ 0\leq x\leq1,\ y\geq0,\ xy\geq1\}.
$$

This set is nonempty since $(0,1,1)'\in\Delta$. It is closed: every constraint
is the inverse image of a closed set under a continuous coordinate or polynomial
map. The last two constraints imply $x>0$, so it is equivalently

$$
\Delta=\{(0,x,y)':0<x\leq1,\ y\geq1/x\}.
$$

It is convex. On the convex domain $(0,1]$, the function $f(x)=1/x$ is convex
because $f''(x)=2/x^3>0$. Its epigraph on that domain is convex, and fixing the
additional coordinate $a=0$ preserves convexity.

Use the paper's equation (4), or equivalently its rearrangement immediately
below equation (6). The pre-treatment constraint is $a=\beta_{pre}=0$;
$\theta=l'(\beta_{post}-\delta_{post})$. Thus

$$
\begin{aligned}
S(0,\Delta)
&=\{\theta:\exists(0,x,y)'\in\Delta,
       \ \theta=(1,0)((0,0)'-(x,y)')\}
&&\text{(identified-set definition)}\\
&=\{\theta:\exists(0,x,y)'\in\Delta,\ \theta=-x\}
&&\text{(evaluate the scalar linear functional)}\\
&=\{-x:0<x\leq1,\ \exists y\geq1/x\}
&&\text{(substitute the equivalent restriction set)}\\
&=\{-x:0<x\leq1\}
&&\text{(each such }x\text{ admits }y=1/x\text{)}\\
&=[-1,0)
&&\text{(image under multiplication by }-1\text{).}
\end{aligned}
$$

For any feasible restriction vector, choose
$\tau_{pre}=0$ and $\tau_{post}=(-x,-y)'$. Then
$\beta=\delta+(0,\tau_{post}')'$ exactly, so the causal decomposition imposes
no missing obstruction in this construction.

The endpoint $0$ cannot belong to the identified set: it would require $x=0$,
contradicting $xy\geq1$. Nevertheless, the feasible sequence
$\delta_n=(0,1/n,n)'$, $n\geq1$, gives $\theta_n=-1/n\to0$.
Therefore the identified set is a bounded, nonempty, nonclosed interval.
The supremum is $0$ but is not a maximum; equivalently the minimum of $l'\delta_{post}$
is not attained. The general closed-interval/extremum formulation does not follow
from the stated closed-convex assumption alone.

## Consequence For Qualification

Retain the valid interval/affine-image argument. Endpoint inclusion additionally
requires attainment: the feasible fibre is convex as the intersection of a convex
set and an affine subspace, so its scalar affine image is convex and hence an
interval, but not necessarily a closed interval. A nonempty compact fibre is
sufficient for attainment. A nonempty
polyhedral fibre with finite optimal values also has attained linear extrema;
polyhedrality alone does not ensure finite bounds. Neither qualification is
silently inserted into the original source or a future agent's prompt.

This finding is a candidate reference/control for assessing assumption fidelity,
not a product rule and not a complete calibration panel. A reviewer may correctly
distinguish this generality issue from the paper's practical polyhedral case.
Published text and executable agreement cannot be used as automatic mathematical
truth. No Q05 completion, accepted agent argument or simulation outcome is claimed.
