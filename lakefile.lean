import Lake
open Lake DSL

package «AIStatistician» where
  moreLeanArgs := #["-DwarningAsError=false"]

require mathlib from git
  "https://github.com/leanprover-community/mathlib4.git"

@[default_target]
lean_lib StatInference where
  roots := #[`StatInference]

