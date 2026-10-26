'use strict';
require('./test_compact_finite_admission.cjs').run({groupIndex:3}).catch(error=>{console.error(error);process.exitCode=1;});
