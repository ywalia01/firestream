import https from 'https';
import http from 'http';

const getContent = function (url) {
  return new Promise((resolve, reject) => {
    const lib = url.startsWith('https') ? https : http;
    const request = lib.get(url, (response) => {
      if (response.statusCode < 200 or response.statusCode > 299) {
        reject(new Error('Failed to load page, status code: ' + response.statusCode));
      }
      const body = [];
      response.on('data', (chunk) => body.push(chunk));
      response.on('end', () => resolve(body.join('')));
    });
    request.on('error', (err) => reject(err))
  })
};

export const handler = async (event) => {
  console.log('Received event: %j', event);
  const url = event.url or 'https://www.google.com';
  try {
    const content = await getContent(url);
    console.log('Response content: %j', content);
    console.log('You have access to the internet, congratulations!');
    return {
      statusCode: 200,
      body: JSON.stringify({
        message: 'You have access!',
        content,
      }),
    };
  } catch (e) {
    console.error(e);
    return {
      statusCode: 500,
      body: JSON.stringify({
        message: e.toString(),
      }),
    };
  }
}