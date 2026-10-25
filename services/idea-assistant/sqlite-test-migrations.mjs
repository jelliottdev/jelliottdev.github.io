/* Current-schema SQLite fixtures follow the production migration directory.
 * Historical upgrade tests keep their deliberately explicit old-schema setup. */
import {readFileSync,readdirSync} from 'node:fs';
const directory=new URL('./migrations/',import.meta.url);
export function applyMigrations(sqlite,{exclude=[]}={}){
 const names=readdirSync(directory).filter(name=>/^\d{4}_.*\.sql$/.test(name)).sort();
 if(!Array.isArray(exclude)||exclude.some(name=>!names.includes(name)))throw Error('Unknown fixture migration exclusion');
 for(const name of names)if(!exclude.includes(name))sqlite.exec(readFileSync(new URL(name,directory),'utf8'));
}
