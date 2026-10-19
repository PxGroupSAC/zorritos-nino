#!/usr/bin/env python3
"""Regenera index.html (documento completo) a partir de zorritos-nino-mapa-peligro.html (fragmento para el artefacto de Claude)."""
import os, sys
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src=os.path.join(root,'zorritos-nino-mapa-peligro.html'); dst=os.path.join(root,'index.html')
s=open(src,encoding='utf-8').read()
i=s.index('</style>')+len('</style>')
doc='<!doctype html>\n<html lang="es">\n<head>\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'+s[:i]+'\n</head>\n<body>\n'+s[i:]+'\n</body>\n</html>\n'
open(dst,'w',encoding='utf-8').write(doc)
print('index.html', round(len(doc)/1e6,2), 'MB')
