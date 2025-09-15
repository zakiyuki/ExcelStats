function main() {
    console.log("main start")

}

function upload() {
    console.log("upload start")
    // ファイルをサーバーに送信する
    const file = fileInput.files[0];
    const formData = new FormData();

    formData.append('file', file);

    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/upload', true);
    xhr.onload = () => {
        if (xhr.status === 200) {
            console.log('File uploaded successfully!');
        } else {
            console.error('Upload failed.');
        }
    };
    xhr.send(formData);
}


document.getElementById('myButton').addEventListener('click', function() {
        const value = document.getElementById('inputValue').value;
        fetch('/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ value: value })
        })
        .then(response => response.json())
        .then(data => {
            document.getElementById('result').innerText = data.result;
        });
    });