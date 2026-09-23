// Different CSS formatting required for specific font
document.fonts.ready.then(() => {
    if (document.fonts.check('14px "ImperialSansText"')) {
        const infSymbol = document.getElementById('inf');

        if (infSymbol) {
            infSymbol.id = 'inf-imperialsans';
        }
    }
});