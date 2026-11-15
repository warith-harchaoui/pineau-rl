"""pineau_rl: the reusable pieces of "Reinforcement Learning: Did we listen to Joelle Pineau in 2018?".

    pineau_rl.stats      Wilson, Newcombe, Fisher, Holm, Cochran-Armitage, Cohen's kappa, Henderson's statistic
    pineau_rl.bootstrap  IQM and probability of improvement with rliable's stratified bootstrap intervals
    pineau_rl.runs       the run format (one CSV per algorithm, task and seed), its reader and a grid loader
    pineau_rl.grid       the reading grid: reading files, harmonisation, final values, validation

The submodules are imported on demand: `import pineau_rl.stats` does not load rliable.
"""
__version__ = "1.0.0"
