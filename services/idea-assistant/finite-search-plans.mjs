/* Backend compatibility entry; browser and server compile identical programs. */
import Compiler from '../../finite-search-compiler.js';
export const LIMITS=Compiler.LIMITS;
export const compileFiniteSearch=Compiler.compile;
