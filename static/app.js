function searchRecipe() {
    let query = document.getElementById("searchInput").value;

    if (!query) {
        alert("لطفاً نام غذا را وارد کنید!");
        return;
    }

    fetch(`/search?query=${query}`)
        .then(response => response.json())
        .then(data => {
            let resultsDiv = document.getElementById("results");
            resultsDiv.innerHTML = "";

            data.forEach(recipe => {
                let recipeDiv = document.createElement("div");
                recipeDiv.innerHTML = `
                    <img src="${recipe.image}" alt="${recipe.title}" width="100">
                    <h3>${recipe.title}</h3>
                `;
                resultsDiv.appendChild(recipeDiv);
            });
        })
        .catch(error => console.error("Error:", error));
}
