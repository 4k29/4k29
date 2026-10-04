// Parse a small mathematical language. Never execute input as JavaScript.
function arithmetic(input){
 const source=input.replace(/\s/g,''),tokens=source.match(/(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?|[+\-*/^()%]/gi)||[];
 if(tokens.join('')!==source||tokens.length>120)throw Error('unsupported');let position=0;
 const peek=()=>tokens[position],take=()=>tokens[position++];
 function primary(){if(peek()==='('){take();const n=sum();if(take()!==')')throw Error('parenthesis');return n;}const token=take();if(!token||!/^\d|^\./.test(token))throw Error('number');return Number(token);}
 function power(){let value=primary();if(peek()==='^'){take();value=Math.pow(value,unary());}return value;}
 function unary(){if(peek()==='+'){take();return unary();}if(peek()==='-'){take();return -unary();}return power();}
 function product(){let value=unary();while(['*','/','%'].includes(peek())){const op=take(),right=unary();if((op==='/'||op==='%')&&right===0)throw Error('zero');value=op==='*'?value*right:op==='/'?value/right:value%right;}return value;}
 function sum(){let value=product();while(['+','-'].includes(peek())){const op=take(),right=product();value=op==='+'?value+right:value-right;}return value;}
 const value=sum();if(position!==tokens.length||!Number.isFinite(value)||Math.abs(value)>1e15)throw Error('range');return value;
}
const format=n=>Object.is(n,-0)?'0':Number(n.toPrecision(12)).toString();
const units={mm:['length',.001],cm:['length',.01],m:['length',1],km:['length',1000],mg:['mass',.000001],g:['mass',.001],kg:['mass',1],ml:['volume',.001],l:['volume',1],秒:['time',1],分:['time',60],時間:['time',3600],s:['time',1],min:['time',60],h:['time',3600]};
function result(input,text,language,details=text){let hash=2166136261;for(const c of input)hash=Math.imul(hash^c.charCodeAt(0),16777619)>>>0;return {id:'calculation-'+hash.toString(16),topic:'calculation',aliases:[],ja:{value:'計算結果',relation:'knowledge',answer:text,detail:details},en:{value:'Calculation',relation:'knowledge',answer:text,detail:details},language,source:{kind:'deterministic-calculation'}};}
export function calculateQuestion(raw){
 const language=/[ぁ-んァ-ヶ一-龠]/.test(raw)?'ja':'en';let text=raw.normalize('NFKC').toLowerCase().trim().replace(/[?？。!！]+$/,'');
 text=text.replace(/^(?:計算して|計算|calculate|compute|what is|what's)\s*[:：]?\s*/,'').replace(/(?:を)?(?:計算して(?:ください)?|計算|求めて|はいくつ|は何|いくつ|教えて|お願い(?:します)?)$/,'').trim();
 const conversion=text.match(/^([+-]?\d+(?:\.\d+)?)\s*(mm|cm|km|m|mg|kg|g|ml|l|秒|分|時間|min|s|h)\s*(?:は何|は|を|から|to|in|=)\s*(mm|cm|km|m|mg|kg|g|ml|l|秒|分|時間|min|s|h)(?:に(?:変換)?|にして|ですか)?$/);
 if(conversion){const [,number,from,to]=conversion;if(units[from][0]!==units[to][0])return result(raw,language==='ja'?'長さ・質量・時間など、同じ種類の量同士で変換してください。':'Convert between units of the same dimension.',language);const answer=format(Number(number)*units[from][1]/units[to][1]);return result(raw,`${number}${from} = ${answer}${to}`,language);}
 const percentage=text.match(/^([+-]?\d+(?:\.\d+)?)\s*(?:の|of)\s*([+-]?\d+(?:\.\d+)?)\s*%(?:は)?$/);
 if(percentage){const [,number,percent]=percentage;const answer=format(Number(number)*Number(percent)/100);return result(raw,`${number} × ${percent} ÷ 100 = ${answer}`,language);}
 const list=text.match(/^(?:平均|中央値|average|mean|median)\s*(?:は|of|:|：)?\s*([+\-\d.,、\s]+)$/);
 if(list){const numbers=list[1].split(/[,、\s]+/).filter(Boolean).map(Number);if(numbers.length<1||numbers.length>100||numbers.some(n=>!Number.isFinite(n)))return null;const median=/中央値|median/.test(text),sorted=[...numbers].sort((a,b)=>a-b),n=numbers.length,value=median?n%2?sorted[(n-1)/2]:(sorted[n/2-1]+sorted[n/2])/2:numbers.reduce((a,b)=>a+b,0)/n;return result(raw,`${median?(language==='ja'?'中央値':'Median'):(language==='ja'?'平均':'Mean')}: ${format(value)}`,language,median?`${sorted.join(', ')} → ${format(value)}`:`(${numbers.join(' + ')}) ÷ ${n} = ${format(value)}`);}
 const expression=text.replace(/[×✕]/g,'*').replace(/[÷]/g,'/').replace(/[−–]/g,'-').replace(/[=＝]+$/,'').trim();
 if(!/^[\d.e+\-*/^()%\s]+$/.test(expression)||!/[\d]/.test(expression)||!/[+\-*/^%]/.test(expression))return null;
 try{return result(raw,`${expression.replace(/\*/g,'×').replace(/\//g,'÷')} = ${format(arithmetic(expression))}`,language);}catch(error){return result(raw,language==='ja'?(error.message==='zero'?'0で割る計算は定義できません。':'計算式の括弧や数値の範囲を確認してください。'):(error.message==='zero'?'Division by zero is undefined.':'Check the expression and numeric range.'),language);}
}
