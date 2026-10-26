'use strict';
require('./test_compact_finite_admission.cjs').run({groupIndex:2}).catch(error=>{console.error(error);process.exitCode=1;});
