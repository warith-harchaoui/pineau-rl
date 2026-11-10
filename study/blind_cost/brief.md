*Version française : [brief-fr.md](brief-fr.md).*

# Rating brief (identical for the three raters, PROTOCOL.md, écart 21 b)

You are rating reporting and evaluation practices found in experimental deep reinforcement learning papers.
You have no data and need none: rate each practice from its definition alone, from your knowledge of how
such papers are written. Do not look anything up and do not read any file.

Picture an author who has already run the main experiments of a paper and has the main results in hand.
For each practice below, give two integers from 1 to 5:

- **C, cost**: the extra work or compute this author must spend to meet the practice.
  1 = a sentence, a table or a link to something that already exists; 3 = some extra analysis or a few
  extra runs; 5 = many new training runs or a large new body of work.
- **R, risk to the conclusion**: how likely meeting the practice is to weaken or overturn the paper's main
  claim (for instance by showing that the gain is not significant, or smaller than reported).
  1 = it cannot affect the claim; 3 = it sometimes does; 5 = it often does.

The practices (each one is what a paper must do to be coded "yes"):

1. **Q3**: gives all the hyperparameters of the proposed method, in a table or paragraph.
2. **Q4**: gives all the hyperparameters of the baselines it compares against.
3. **Q5**: links to its code in the paper ("available on request" or "will be released" does not count).
4. **Q6**: describes how the hyperparameters were chosen (grid, random search, budget, criterion); "tuned" alone does not count.
5. **Q7**: evaluates on tasks, environments, environment random seeds or data not seen during training or tuning.
6. **Q8**: applies a statistical test to a comparison (t-test, Welch, Mann-Whitney, bootstrap with interval, stratified IQM intervals); error bars alone do not count.
7. **X2**: reports an uncertainty (error bars, standard deviation, interval) on the main results.
8. **X3 (reversed)**: does NOT select its best runs (no "top-k", no "best of N", no best checkpoint chosen on the test set).
9. **X4**: tunes its baselines with the same care as its method, and says so (a tuning procedure described for the baselines, or an equal tuning budget announced).
10. **X7**: quantifies the compute used (hours, GPU-hours, FLOPs, or a number of GPUs with a duration); naming the hardware alone does not count.
11. **Y1**: defines the performance measure reported (final score, average of the last episodes, area under the curve, and at which point of training it is measured).
12. **Y5**: identifies the implementation (code base) used for each baseline.
13. **Y7**: gives the version of every environment or benchmark used.
14. **Y8**: runs a generalisation test outside the training conditions (tasks, dynamics or data absent from training).
15. **Y9**: shows the sensitivity of the method to at least one hyperparameter (a sweep with its results; a component ablation does not count).
16. **Y10**: lists its software dependencies with their versions.
17. **Y12**: uses a statistical tool from after 2018 (interquartile mean, rliable, performance profiles, probability of improvement).

Answer with a JSON object only, no prose, of the form
`{"Q3": {"C": 1, "R": 1, "why": "one short sentence"}, ...}` with all 17 keys.
