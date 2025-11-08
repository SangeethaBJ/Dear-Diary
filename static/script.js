// Page turning animation could be enhanced later
document.querySelectorAll('.genre').forEach(el=>{
  el.addEventListener('click', e=>{
    document.querySelector('.page').style.transform='rotateY(90deg)';
    setTimeout(()=>{document.querySelector('.page').style.transform='rotateY(0deg)';},300);
  });
});
