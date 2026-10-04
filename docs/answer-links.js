// Link restrictions belong to the clause that requested this fact.
export function linksForFact(fact,analyses){
 const requests=analyses.filter(a=>!a.unknown&&a.factIds?.includes(fact.id));
 if(!requests.length)return [];
 return (fact.links||[]).filter(link=>requests.some(a=>a.mode==='favorite-youtube'?link.channel==='youtube':a.mode==='favorite-x'?link.channel==='x':true));
}
