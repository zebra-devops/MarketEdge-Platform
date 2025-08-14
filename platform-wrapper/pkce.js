const crypto = require('crypto');

// Generate code verifier (random string)
function generateCodeVerifier() {
  return crypto.randomBytes(32).toString('base64url');
}

// Generate code challenge from verifier
function generateCodeChallenge(verifier) {
  return crypto.createHash('sha256').update(verifier).digest('base64url');
}

// Generate both
const codeVerifier = generateCodeVerifier();
const codeChallenge = generateCodeChallenge(codeVerifier);

console.log('Code Verifier:', codeVerifier);
console.log('Code Challenge:', codeChallenge);
console.log('\n--- Use these in your flow ---');
console.log(`1. Authorization URL should include: code_challenge=${codeChallenge}&code_challenge_method=S256`);
console.log(`2. Token exchange should include: code_verifier=${codeVerifier}`);