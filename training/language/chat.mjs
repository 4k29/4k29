// Command-line continuation, never an owner QA answer catalogue.
import {pathToFileURL} from 'node:url';
import {createDialogueDecoder} from '../dialogue/inference.mjs';
const [modelPath,...openingParts]=process.argv.slice(2);
if(!modelPath||!openingParts.length)throw Error('Usage: node training/language/chat.mjs /absolute/model.js 日本語の書き出し');
const {dialogueModel:model}=await import(pathToFileURL(modelPath));
const decoder=createDialogueDecoder(model,{tokenizerAlgorithm:'adjacent-heap'});
const opening=openingParts.join(' '),result=decoder.generateRaw(opening);
console.log(JSON.stringify({opening,...result},null,2));
