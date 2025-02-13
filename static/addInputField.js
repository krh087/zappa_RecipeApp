function addInputFields() {
    const container = document.getElementById("dynamic-input-container");

    // 材料名の入力欄
    const nameInput = document.createElement("input");
    nameInput.type = "text";
    nameInput.name = "dynamic_ingredient"; // Flaskで受け取るための名前
    nameInput.placeholder = "（例）パスタ";

    // 分量の入力欄
    const ageInput = document.createElement("input");
    ageInput.type = "text";
    ageInput.name = "dynamic_quantity"; // Flaskで受け取るための名前
    ageInput.placeholder = "（例）100g";

    // コンテナに追加
    container.appendChild(nameInput);
    container.appendChild(ageInput);
    container.appendChild(document.createElement("br")); // 改行
}
function addInputFields2() {
    const container = document.getElementById("dynamic-input-container2");

    // 手順の入力欄
    const addressInput = document.createElement("input");
    addressInput.type = "text";
    addressInput.name = "dynamic_instruction"; // Flaskで受け取るための名前
    addressInput.placeholder = "(例)にんにくを刻み、オイルとにんにくを弱火で炒める";

    // コンテナに追加
    container.appendChild(addressInput);
    container.appendChild(document.createElement("br")); // 改行
}
