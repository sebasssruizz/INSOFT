# ENCUESTA_USABILIDAD — borrador para el piloto

- Duración: **3–4 minutos**, anónima, una respuesta por estudiante.
- Aplicación en persona o con link: **16-oct (t0)** y **24/31-oct (t final)**.
- Escala SUS: 1 = Totalmente en desacuerdo … 5 = Totalmente de acuerdo.

## BLOQUE 1 — SUS (usabilidad general de la plataforma)

1. Creo que usaré esta plataforma con frecuencia. 1..5
2. La plataforma se siente innecesariamente compleja. 1..5  *(invertida)*
3. La plataforma era fácil de usar. 1..5
4. Necesité ayuda de otra persona para empezar. 1..5  *(invertida)*
5. Las funciones estuvieron bien integradas. 1..5
6. Encontré funciones demasiado inconsistentes. 1..5  *(invertida)*
7. Creo que la mayoría aprendería a usarla rápido. 1..5
8. El sistema se sentía engorroso. 1..5  *(invertida)*
9. Me sentí con confianza al usarla. 1..5
10. Necesité aprender muchas cosas antes de poder usarla. 1..5  *(invertida)*

## BLOQUE 2 — repaso (miniquiz)

11. El repaso me ayudó a fijar lo leído (términos técnicos carreras claves). 1..5
12. Ver la explicación después de responder me pareció útil. 1..5
13. Hubo preguntas relacionadas con el contenido de la unidad. 1..5

## BLOQUE 3 — asistente IA

14. Las respuestas del asistente fueron útiles para mi estudio. 1..5
15. El asistente respondió dentro de un tiempo razonable. 1..5
16. Al no estar la IA siempre pude seguir estudiando con las "respuestas de respaldo". 1..5

## BLOQUE 4 — modo práctica

17. El modo práctica me animó a repasar más de lo que haría por mi cuenta. 1..5
18. Las preguntas de práctica estuvieron enfocadas en mis debilidades. 1..5

## BLOQUE 5 — abierto (texto libre, opcional)

19. ¿Qué usarías o cambiarías primero y por qué?
20. ¿Algo que te confundió, te bloqueó o te pareció injusto?
21. ¿Qué parte explota más en el examen, repaso, práctica o asistente?
22. ¿Alguna expresión o texto que no entiendas, digamos lo frecuente para tus amigos?

## Export y score

- `scripts/score_sus.py pedidos.csv` imprime la puntuación SUS media (0-100)
  por répondiente y grupo, marcando invertidas (2,4,6,8,10).
- Umbral de éxito del curso: SUS ≥ 68 (arriba de la media de 68).
