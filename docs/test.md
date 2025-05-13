# API Connection Test

Use the button below to test the connection to the Domain API.

<div class="api-test">
  <button id="testButton" onclick="testConnection()">Test Connection</button>
  <div id="result" class="result-box"></div>
</div>

<style>
.api-test {
  padding: 20px;
  background: #f5f5f5;
  border-radius: 8px;
  margin: 20px 0;
}

#testButton {
  background: #2196F3;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
}

#testButton:hover {
  background: #1976D2;
}

.result-box {
  margin-top: 20px;
  padding: 15px;
  border-radius: 4px;
  background: white;
  min-height: 50px;
  display: none;
}

.success {
  border-left: 4px solid #4CAF50;
}

.error {
  border-left: 4px solid #f44336;
}
</style>

<script>
async function testConnection() {
  const button = document.getElementById('testButton');
  const resultDiv = document.getElementById('result');
  
  button.disabled = true;
  button.textContent = 'Testing...';
  resultDiv.style.display = 'block';
  resultDiv.innerHTML = 'Connecting to API...';
  resultDiv.className = 'result-box';
  
  try {
    const response = await fetch('http://127.0.0.1:8000/test-domain');
    const data = await response.json();
    
    if (data.success) {
      resultDiv.className = 'result-box success';
      resultDiv.innerHTML = '<strong>Success!</strong><br>Connected to Domain API successfully.<br><pre>' + 
        JSON.stringify(data.data, null, 2) + '</pre>';
    } else {
      resultDiv.className = 'result-box error';
      resultDiv.innerHTML = '<strong>Error:</strong><br>' + data.error;
    }
  } catch (error) {
    resultDiv.className = 'result-box error';
    resultDiv.innerHTML = '<strong>Connection Error:</strong><br>Failed to connect to the API server. Make sure it\'s running locally.';
  }
  
  button.disabled = false;
  button.textContent = 'Test Connection';
}
</script>
