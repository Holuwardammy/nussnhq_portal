// registration.js

// Searchable School Dropdown
const searchInput = document.getElementById("school-search");
const schoolList = document.getElementById("school-list");
const schoolSelected = document.getElementById("school-selected");
const schools = schoolList.getElementsByTagName("li");

// Show list when input is focused
searchInput.addEventListener("focus", () => {
    schoolList.style.display = "block";
});

// Filter schools as user types
searchInput.addEventListener("input", () => {
    let filter = searchInput.value.toUpperCase();
    for (let i = 0; i < schools.length; i++) {
        let txtValue = schools[i].textContent || schools[i].innerText;
        schools[i].style.display = txtValue.toUpperCase().indexOf(filter) > -1 ? "" : "none";
    }
});

// When a school is clicked
for (let i = 0; i < schools.length; i++) {
    schools[i].addEventListener("click", function() {
        searchInput.value = this.innerText;
        schoolSelected.value = this.innerText;
        schoolList.style.display = "none";
    });
}

// Hide list when clicking outside
document.addEventListener("click", function(event) {
    if (!event.target.closest(".searchable-select")) {
        schoolList.style.display = "none";
    }
});