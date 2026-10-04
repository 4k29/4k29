// Filter authored framing, never the protected factual value supplied later.
// Answers speak directly as the profile owner rather than reporting a profile.
export function directVoicePath(path,vocabulary){
 return !/プロフィール|登録|本人|挙げ|述べ|紹介|\bin my profile\b|\b(?:listed|registered|recorded)\b/i.test(path.tokens.map(id=>vocabulary[id]).join(''));
}
