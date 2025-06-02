#!/usr/bin/env node

// Test MCP protocol communication
const { spawn } = require('child_process');

async function testMCPProtocol() {
  console.log('🧪 Тестирование MCP протокола...\n');
  
  try {
    // Start MCP server
    const mcpServer = spawn('node', ['dist/index.js'], {
      stdio: ['pipe', 'pipe', 'pipe'],
      env: {
        ...process.env,
        PUBMED_API_KEY: 'c3dec23f21707809b6c685a2b708fc75ab08',
        PUBMED_API_BASE_URL: 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/',
        PUBMED_RATE_LIMIT_RPM: '600',
        PUBMED_TIMEOUT_MS: '30000',
        LOG_LEVEL: 'info'
      }
    });

    let responseData = '';
    
    mcpServer.stdout.on('data', (data) => {
      responseData += data.toString();
    });

    mcpServer.stderr.on('data', (data) => {
      console.log('Server stderr:', data.toString());
    });

    // Send initialize request
    const initRequest = {
      jsonrpc: "2.0",
      id: 1,
      method: "initialize",
      params: {
        protocolVersion: "2024-11-05",
        capabilities: {
          roots: {
            listChanged: true
          },
          sampling: {}
        },
        clientInfo: {
          name: "test-client",
          version: "1.0.0"
        }
      }
    };

    console.log('📤 Отправка initialize запроса...');
    mcpServer.stdin.write(JSON.stringify(initRequest) + '\n');

    // Wait for response
    await new Promise((resolve) => {
      setTimeout(() => {
        console.log('📥 Ответ сервера:');
        console.log(responseData);
        
        if (responseData.includes('tools/list') || responseData.includes('capabilities')) {
          console.log('✅ MCP сервер отвечает правильно!');
        } else {
          console.log('❌ Неожиданный ответ от MCP сервера');
        }
        
        mcpServer.kill();
        resolve();
      }, 3000);
    });

  } catch (error) {
    console.error('❌ Ошибка тестирования MCP:', error);
  }
}

if (require.main === module) {
  testMCPProtocol();
}