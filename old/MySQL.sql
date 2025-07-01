-- DROP TABLE IF EXISTS usuarios;

-- CREATE TABLE usuarios (
--     codigo INTEGER PRIMARY KEY AUTOINCREMENT,
--     nome TEXT NOT NULL,
--     email TEXT NOT NULL UNIQUE,
--     senha_hash TEXT NOT NULL,
--     funcao TEXT,
--     organizacao TEXT,
--     ativo TEXT NOT NULL
-- );

-- INSERT INTO usuarios (
--     codigo, nome, email, senha_hash, funcao, organizacao, ativo
-- ) VALUES (
--     1,
--     'Daniel Leite',
--     'daniel.desproj@gmail.com',
--     '6717b312048b084a711742db766c0e635cdf6a9173a16fb04e05cf0f3f0d9587',
--     'Engenheiro Civil',
--     'LNEC',
--     'sim'
-- );

-- CREATE TABLE IF NOT EXISTS barragens (
--     Barragem_ID INTEGER PRIMARY KEY AUTOINCREMENT,
--     Usuario_ID INTEGER NOT NULL,
--     Nome TEXT NOT NULL,
--     Tipo TEXT NOT NULL,
--     Fundacao TEXT,
--     Localizacao TEXT,
--     FOREIGN KEY (Usuario_ID) REFERENCES usuarios(id)
-- );

-- CREATE TABLE barragens (
--     Barragem_ID INTEGER PRIMARY KEY AUTOINCREMENT,
--     Usuario_ID INTEGER NOT NULL,
--     Nome TEXT NOT NULL,
--     Tipo TEXT NOT NULL,
--     TipoFundacao TEXT,
--     Localizacao TEXT,
--     FOREIGN KEY (Usuario_ID) REFERENCES usuarios(codigo)
-- )

-- ALTER TABLE usuarios ADD COLUMN is_admin INTEGER DEFAULT 0

-- Tabelas de Classificação (Enumeradas)



-- CREATE TABLE classificacoes_suscetibilidade (
--     id INTEGER PRIMARY KEY,
--     nome TEXT UNIQUE NOT NULL,  -- 'Baixa', 'Média', 'Alta', 'Crítica'
--     peso INTEGER NOT NULL
-- );

-- CREATE TABLE niveis_risco (
--     id INTEGER PRIMARY KEY,
--     nivel TEXT UNIQUE NOT NULL,  -- 'Baixo', 'Moderado', 'Alto', 'Crítico'
--     cor_alerta TEXT NOT NULL,    -- Código hex para visualização
--     acao_recomendada TEXT NOT NULL
-- );


-- DROP TABLE IF EXISTS tipos_barragem;

-- Tabelas Principais
-- CREATE TABLE tipos_barragem (
--     id INTEGER PRIMARY KEY,
--     nome TEXT UNIQUE NOT NULL,
--     descricao TEXT,
--     caracteristicas_principais TEXT,
--     referencia_tecnica TEXT
-- );

-- DROP TABLE IF EXISTS tipos_fundacao;
-- CREATE TABLE tipos_fundacao (
--     id INTEGER PRIMARY KEY,
--     nome TEXT UNIQUE NOT NULL,
--     descricao TEXT,
--     caracteristicas TEXT,
--     referencia_tecnica TEXT
-- );

-- CREATE TABLE tipos_materiais (
--     id INTEGER PRIMARY KEY,
--     nome TEXT UNIQUE NOT NULL,
--     descricao TEXT,
--     classificacao_unificada TEXT,
--     propriedades_json TEXT  -- Armazena propriedades como JSON
-- );

-- CREATE TABLE condicoes_criticas (
--     id INTEGER PRIMARY KEY,
--     nome TEXT UNIQUE NOT NULL,
--     tipo_condicao TEXT NOT NULL,  -- 'Hidrológica', 'Geológica', etc.
--     descricao TEXT,
--     referencia_tecnica TEXT
-- );

-- DROP TABLE IF EXISTS modos_falha;
-- CREATE TABLE modos_falha (
--     id INTEGER PRIMARY KEY,
--     codigo TEXT UNIQUE NOT NULL,  -- Ex: 'MF-001'
--     nome TEXT NOT NULL,
--     descricao TEXT NOT NULL,
--     mecanismo TEXT NOT NULL,
--     fase_operacao TEXT NOT NULL,  -- 'Construção', 'Operação', 'Todos'
--     referencia_tecnica TEXT
-- );

-- Tabelas de Relacionamento com Rastreabilidade
-- CREATE TABLE barragem_modos_falha (
--     id INTEGER PRIMARY KEY,
--     tipo_barragem_id INTEGER NOT NULL,
--     modo_falha_id INTEGER NOT NULL,
--     relevancia INTEGER CHECK(relevancia BETWEEN 1 AND 5),
--     fonte TEXT NOT NULL,
--     observacoes TEXT,
--     FOREIGN KEY (tipo_barragem_id) REFERENCES tipos_barragem(id),
--     FOREIGN KEY (modo_falha_id) REFERENCES modos_falha(id),
--     UNIQUE(tipo_barragem_id, modo_falha_id)
-- );

-- CREATE TABLE fundacao_modos_falha (
--     id INTEGER PRIMARY KEY,
--     tipo_fundacao_id INTEGER NOT NULL,
--     modo_falha_id INTEGER NOT NULL,
--     relevancia INTEGER CHECK(relevancia BETWEEN 1 AND 5),
--     fonte TEXT NOT NULL,
--     FOREIGN KEY (tipo_fundacao_id) REFERENCES tipos_fundacao(id),
--     FOREIGN KEY (modo_falha_id) REFERENCES modos_falha(id),
--     UNIQUE(tipo_fundacao_id, modo_falha_id)
-- );

-- CREATE TABLE falha_materiais_suscetiveis (
--     id INTEGER PRIMARY KEY,
--     modo_falha_id INTEGER NOT NULL,
--     material_id INTEGER NOT NULL,
--     suscetibilidade_id INTEGER NOT NULL,
--     mecanismo_especifico TEXT,
--     fonte TEXT NOT NULL,
--     FOREIGN KEY (modo_falha_id) REFERENCES modos_falha(id),
--     FOREIGN KEY (material_id) REFERENCES tipos_materiais(id),
--     FOREIGN KEY (suscetibilidade_id) REFERENCES classificacoes_suscetibilidade(id),
--     UNIQUE(modo_falha_id, material_id)
-- );

-- CREATE TABLE falha_condicoes_criticas (
--     id INTEGER PRIMARY KEY,
--     modo_falha_id INTEGER NOT NULL,
--     condicao_id INTEGER NOT NULL,
--     peso_relativo INTEGER CHECK(peso_relativo BETWEEN 1 AND 5),
--     fonte TEXT NOT NULL,
--     FOREIGN KEY (modo_falha_id) REFERENCES modos_falha(id),
--     FOREIGN KEY (condicao_id) REFERENCES condicoes_criticas(id),
--     UNIQUE(modo_falha_id, condicao_id)
-- );

-- Tabelas para Anomalias (Sinais de Campo)

-- CREATE TABLE categorias_anomalias (
--     id INTEGER PRIMARY KEY,
--     nome TEXT UNIQUE NOT NULL  -- 'Estrutural', 'Hidráulica', 'Geotécnica'
-- );

-- CREATE TABLE localizacoes_anomalias (
--     id INTEGER PRIMARY KEY,
--     nome TEXT UNIQUE NOT NULL  -- 'Corpo', 'Fundação', 'Encontro', 'Jusante'
-- );

-- DROP TABLE IF EXISTS anomalias;
-- CREATE TABLE anomalias (
--     id INTEGER PRIMARY KEY,
--     codigo TEXT UNIQUE NOT NULL,  -- Ex: 'ANOM-001'
--     nome TEXT NOT NULL,
--     descricao TEXT NOT NULL,
--     categoria_id INTEGER NOT NULL,
--     localizacao_id INTEGER NOT NULL,
--     gravidade_padrao INTEGER,  -- 1-5 escala
--     referencia_tecnica TEXT,
--     FOREIGN KEY (categoria_id) REFERENCES categorias_anomalias(id),
--     FOREIGN KEY (localizacao_id) REFERENCES localizacoes_anomalias(id)
-- );

-- CREATE TABLE falha_anomalias (
--     id INTEGER PRIMARY KEY,
--     modo_falha_id INTEGER NOT NULL,
--     anomalia_id INTEGER NOT NULL,
--     importancia INTEGER CHECK(importancia BETWEEN 1 AND 5),
--     frequencia_ocorrencia TEXT,  -- 'Rara', 'Ocasional', 'Comum'
--     fonte TEXT NOT NULL,
--     FOREIGN KEY (modo_falha_id) REFERENCES modos_falha(id),
--     FOREIGN KEY (anomalia_id) REFERENCES anomalias(id),
--     UNIQUE(modo_falha_id, anomalia_id)
-- );

-- -- Tabela de Critérios de Risco Dinâmicos
-- CREATE TABLE criterios_risco (
--     id INTEGER PRIMARY KEY,
--     modo_falha_id INTEGER NOT NULL,
--     nivel_risco_id INTEGER NOT NULL,
--     pontuacao_minima INTEGER NOT NULL,
--     acao_especifica TEXT,
--     FOREIGN KEY (modo_falha_id) REFERENCES modos_falha(id),
--     FOREIGN KEY (nivel_risco_id) REFERENCES niveis_risco(id)
-- );

-- -- Tabela de Casos Históricos com Relacionamento
-- CREATE TABLE casos_historicos (
--     id INTEGER PRIMARY KEY,
--     referencia TEXT UNIQUE NOT NULL,  -- Ex: 'LNEC-1985'
--     titulo TEXT NOT NULL,
--     descricao TEXT,
--     ano_ocorrencia INTEGER,
--     consequencias TEXT,
--     licoes_aprendidas TEXT,
--     fonte_primaria TEXT
-- );

-- CREATE TABLE historico_modos_falha (
--     id INTEGER PRIMARY KEY,
--     caso_id INTEGER NOT NULL,
--     modo_falha_id INTEGER NOT NULL,
--     confirmacao TEXT,  -- 'Confirmado', 'Suspeito', 'Principal'
--     FOREIGN KEY (caso_id) REFERENCES casos_historicos(id),
--     FOREIGN KEY (modo_falha_id) REFERENCES modos_falha(id)
-- );

-- DROP TABLE IF EXISTS barragens;
-- CREATE TABLE IF NOT EXISTS barragens (
--             id INTEGER PRIMARY KEY AUTOINCREMENT,
--             usuario_id TEXT NOT NULL,
--             nome TEXT NOT NULL,
--             tipo TEXT NOT NULL,
--             fundacao TEXT NOT NULL,
--             localizacao TEXT,
--             em_analise INTEGER DEFAULT 0,
--             data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--             FOREIGN KEY (usuario_id) REFERENCES usuarios (codigo)
--         );


-- INSERT INTO tipos_materiais (nome, descricao, classificacao_unificada, propriedades_json)
-- VALUES
-- ('Argila Impermeável', 'Material fino usado como núcleo impermeável', 'CL', '{"peso_especifico": "18 kN/m³", "permeabilidade": "1e-9 m/s"}'),
-- ('Areia Fina', 'Usada em zonas de transição e filtros', 'SM', '{"peso_especifico": "17.5 kN/m³", "permeabilidade": "1e-5 m/s"}'),
-- ('Areia Grossa', 'Usada como camada de filtração', 'SW', '{"peso_especifico": "18.2 kN/m³", "permeabilidade": "1e-4 m/s"}'),
-- ('Pedregulho', 'Camada estrutural e drenagem', 'GW', '{"peso_especifico": "19 kN/m³", "permeabilidade": "1e-2 m/s"}'),
-- ('Enrocamento', 'Blocos grandes de rocha, usado em paramentos externos', 'GP', '{"peso_especifico": "21 kN/m³", "permeabilidade": "1e-1 m/s"}'),
-- ('Solo-Cimento', 'Material estabilizado usado em núcleos ou cortinas', 'SC', '{"peso_especifico": "19.5 kN/m³", "resistencia_compressao": "2 MPa"}'),
-- ('Geotêxtil', 'Material sintético usado como filtro ou separação', NULL, '{"tipo": "não tecido", "gramatura": "300 g/m²"}'),
-- ('Betão Armado', 'Concreto reforçado usado em barragens de gravidade', NULL, '{"resistencia_compressao": "30 MPa", "modulo_elasticidade": "30 GPa"}'),
-- ('Brita 0', 'Agregado granular usado em camadas de suporte', 'GP', '{"tamanho_medio": "25 mm", "permeabilidade": "5e-3 m/s"}');

-- INSERT INTO condicoes_criticas (nome, tipo_condicao, descricao, referencia_tecnica) VALUES
-- ('Infiltração Acelerada', 'Hidráulica', 'Aumento repentino no fluxo de água através do corpo da barragem.', 'ICOLD Bulletin 99'),
-- ('Pressão de Poros Elevada', 'Hidráulica', 'Incremento excessivo da pressão intersticial nos materiais do núcleo.', 'ABGE – Manual de Geotecnia'),
-- ('Deslizamento Interno', 'Geotécnica', 'Movimento relativo entre camadas internas da barragem.', 'NRB 11682'),
-- ('Recalque Diferencial', 'Geotécnica', 'Assentamento desigual entre diferentes seções da barragem.', 'USBR Design Standards'),
-- ('Perda de Material Fino', 'Hidráulica', 'Migração de finos com o fluxo de água através do maciço.', 'ICOLD Bulletin 52'),
-- ('Vegetação Invasiva', 'Manutenção', 'Presença de raízes profundas que podem criar caminhos preferenciais de percolação.', 'ANA Manual de Inspeção'),
-- ('Fissura Longitudinal no Talude', 'Estrutural', 'Fissura paralela ao eixo da barragem, indicando possíveis instabilidades.', 'CETESB Relatório Técnico 2020'),
-- ('Obstrução do Dreno', 'Manutenção', 'Entupimento do sistema de drenagem, elevando o nível piezométrico.', 'DNPM – Diretrizes Técnicas de Segurança'),
-- ('Vazão Anormal em Descarga de Fundo', 'Operacional', 'Vazamento ou fluxo fora dos padrões na saída de fundo.', 'IBAMA Diretrizes para Segurança de Barragens');


-- DROP TABLE IF EXISTS categorias_anomalias;
-- DROP TABLE IF EXISTS localizacoes_anomalias;

-- -- Criação das tabelas relacionadas (se não existirem)
-- CREATE TABLE IF NOT EXISTS categorias_anomalias (
--     id INTEGER PRIMARY KEY,
--     nome TEXT UNIQUE NOT NULL,
--     descricao TEXT
-- );

-- CREATE TABLE IF NOT EXISTS localizacoes_anomalias (
--     id INTEGER PRIMARY KEY,
--     nome TEXT UNIQUE NOT NULL,
--     descricao TEXT
-- );




-- -- Inserção de categorias de anomalias
-- INSERT INTO categorias_anomalias (id, nome, descricao) VALUES
-- (1, 'Estrutural', 'Anomalias relacionadas à estrutura da barragem'),
-- (2, 'Geotécnica', 'Anomalias relacionadas ao comportamento geotécnico'),
-- (3, 'Hidráulica', 'Anomalias relacionadas ao sistema hidráulico'),
-- (4, 'Instrumentação', 'Anomalias em instrumentos de monitoramento'),
-- (5, 'Vegetação', 'Problemas relacionados à vegetação');

-- -- Inserção de localizações típicas
-- INSERT INTO localizacoes_anomalias (id, nome, descricao) VALUES
-- (1, 'Crista', 'Parte superior da barragem'),
-- (2, 'Talude de Montante', 'Face da barragem voltada para o reservatório'),
-- (3, 'Talude de Jusante', 'Face da barragem voltada para o lado oposto ao reservatório'),
-- (4, 'Fundação', 'Base de apoio da barragem'),
-- (5, 'Sistema de Drenagem', 'Estruturas de drenagem interna'),
-- (6, 'Vertedouro', 'Estrutura de extravasão'),
-- (7, 'Sistema de Instrumentação', 'Pontos de monitoramento');

-- -- Inserção de anomalias (dados de exemplo)
-- INSERT INTO anomalias (id, codigo, nome, descricao, categoria_id, localizacao_id, gravidade_padrao, referencia_tecnica) VALUES
-- -- Anomalias Estruturais
-- (1, 'AN-EST-001', 'Trinca na crista', 'Fissuras longitudinais na crista da barragem', 1, 1, 3, 'DNIT 123/2020'),
-- (2, 'AN-EST-002', 'Deformação do talude', 'Deformação visível no talude de jusante', 1, 3, 4, 'EMBRAPA 456/2019'),

-- -- Anomalias Geotécnicas
-- (3, 'AN-GEO-001', 'Surgência na fundação', 'Aparecimento de água na fundação', 2, 4, 5, 'ABMS 789/2021'),
-- (4, 'AN-GEO-002', 'Erosão interna', 'Indícios de piping ou erosão interna', 2, 5, 5, 'USACE EM 1110-2-1913'),

-- -- Anomalias Hidráulicas
-- (5, 'AN-HID-001', 'Vazamento no vertedouro', 'Vazamento nas juntas do vertedouro', 3, 6, 2, 'ANA Resolução 123/2018'),
-- (6, 'AN-HID-002', 'Assoreamento do extravasor', 'Acúmulo de sedimentos no sistema de extravasão', 3, 6, 3, 'DNIT 789/2020'),

-- -- Anomalias de Instrumentação
-- (7, 'AN-INS-001', 'Falha em piezômetro', 'Piezômetro com leituras inconsistentes', 4, 7, 2, 'ABNT NBR 15495'),
-- (8, 'AN-INS-002', 'Deslocamento de prisma', 'Prisma de controle com deslocamento anômalo', 4, 7, 4, 'ICOLD Bulletin 158'),

-- -- Anomalias de Vegetação
-- (9, 'AN-VEG-001', 'Raízes profundas', 'Presença de vegetação com raízes profundas no talude', 5, 2, 1, 'IBAMA Portaria 321/2017'),
-- (10, 'AN-VEG-002', 'Ausência de vegetação', 'Áreas desprovidas de vegetação no talude de jusante', 5, 3, 2, 'CONAMA Resolução 302/2002'),

-- -- Anomalias adicionais
-- (11, 'AN-EST-003', 'Degradação do concreto', 'Eflorescências e desagregação do concreto', 1, 2, 3, 'ABNT NBR 6118'),
-- (12, 'AN-GEO-003', 'Assentamento diferencial', 'Diferença de recalques na estrutura', 2, 4, 4, 'ABNT NBR 6484'),
-- (13, 'AN-HID-003', 'Bloqueio de dreno', 'Dreno obstruído por sedimentos', 3, 5, 3, 'USBR Design Standards'),
-- (14, 'AN-INS-003', 'Corrosão de instrumento', 'Corrosão avançada em equipamento de monitoramento', 4, 7, 2, 'ASTM G1-03'),
-- (15, 'AN-VEG-003', 'Árvores de grande porte', 'Presença de árvores de grande porte na crista', 5, 1, 2, 'Lei 12.651/2012');


-- ALTER TABLE barragens ADD COLUMN altura REAL;
-- ALTER TABLE barragens ADD COLUMN comprimento REAL;


-- CREATE TABLE IF NOT EXISTS zonas_barragem (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     barragem_id INTEGER NOT NULL,
--     nome TEXT NOT NULL,
--     material_id INTEGER NOT NULL,
--     FOREIGN KEY (barragem_id) REFERENCES barragens(id),
--     FOREIGN KEY (material_id) REFERENCES tipos_materiais(id)
-- );


-- CREATE TABLE IF NOT EXISTS modos_falha_associacoes (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     modo_falha_id INTEGER NOT NULL,
--     tipo_barragem TEXT,
--     zona_nome TEXT,
--     material_id INTEGER,
--     altura_min REAL,
--     altura_max REAL,
--     comprimento_min REAL,
--     comprimento_max REAL,
--     FOREIGN KEY (modo_falha_id) REFERENCES modos_falha(id),
--     FOREIGN KEY (material_id) REFERENCES tipos_materiais(id)
-- );


-- ALTER TABLE barragens DROP COLUMN fundacao;

-- DROP TABLE IF EXISTS barragens;
-- CREATE TABLE IF NOT EXISTS barragens (
--             id INTEGER PRIMARY KEY AUTOINCREMENT,
--             usuario_id INTEGER NOT NULL,
--             nome TEXT NOT NULL,
--             tipo_id INTEGER NOT NULL,
--             localizacao TEXT,
--             altura REAL,
--             comprimento REAL,
--             rel_cordaaltura REAL,
--             em_analise INTEGER DEFAULT 0,
--             data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--             FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
--         );

-- DROP TABLE IF EXISTS tipos_barragem;
-- -- Criação da tabela tipos_barragem
-- CREATE TABLE tipos_barragem (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     usuario_id INTEGER NOT NULL,
--     nome TEXT NOT NULL,
--     descricao TEXT,
--     referencia_tecnica TEXT,
--     image_path TEXT  -- Caminho local ou URL da imagem associada
-- );

-- INSERT INTO tipos_barragem (id, usuario_id, nome, descricao) VALUES
-- (1, 1, 'Homogênea', 'Barragem construída com um único tipo de material'),
-- (2, 1, 'Terra e Enrocamento', 'Barragem com núcleo de terra e envoltório de enrocamento'),
-- (3, 1, 'Enrocamento com Face de Betão', 'Barragem de enrocamento com face de concreto'),
-- (4, 1, 'Enrocamento com Núcleo Betuminoso', 'Barragem de enrocamento com núcleo impermeável de betume');

-- DROP TABLE IF EXISTS zonas_barragem;
-- CREATE TABLE IF NOT EXISTS zonas_barragem (
--             id INTEGER PRIMARY KEY AUTOINCREMENT,
--             usuario_id INTEGER NOT NULL,
--             barragem_id INTEGER NOT NULL,
--             material_id INTEGER NOT NULL,
--             nome TEXT NOT NULL,
--             descricao TEXT,
--             FOREIGN KEY (barragem_id) REFERENCES barragens(id),
--             FOREIGN KEY (material_id) REFERENCES tipos_materiais(id)
--         );


-- CREATE TABLE IF NOT EXISTS tipos_materiais (
--             id INTEGER PRIMARY KEY AUTOINCREMENT,
--             usuario_id INTEGER NOT NULL,
--             nome TEXT NOT NULL,
--             descricao TEXT
--         );


-- CREATE TABLE IF NOT EXISTS tipos_zonas_bar (
--             id INTEGER PRIMARY KEY AUTOINCREMENT,
--             nome TEXT NOT NULL,
--             descricao TEXT
--         );

-- INSERT INTO tipos_zonas_bar (nome, descricao) VALUES
-- -- Zonas Estruturais Principais
-- ('Zona de Comportas', 'Área contendo os sistemas de comportas e mecanismos de controle de vazão'),
-- ('Zona do Maciço', 'Corpo principal da barragem onde ocorrem os esforços estruturais'),
-- ('Zona de Talude de Montante', 'Face da barragem voltada para o reservatório'),
-- ('Zona de Talude de Jusante', 'Face da barragem voltada para o lado oposto ao reservatório'),
-- ('Zona de Fundação', 'Base de apoio da barragem em contato com o terreno natural'),

-- -- Zonas de Interface
-- ('Zona de Contato Terra-Betão', 'Área de transição entre estruturas de diferentes materiais'),
-- ('Zona de Encontro com Margens', 'Áreas laterais onde a barragem se conecta com as margens do vale'),

-- -- Zonas de Proteção
-- ('Zona de Rip-Rap', 'Revestimento de proteção contra erosão nos taludes'),
-- ('Zona de Filtros e Drenos', 'Sistema de filtragem e drenagem interna'),

-- -- Zonas Operacionais
-- ('Zona de Instrumentação', 'Áreas com equipamentos de monitoramento (piezômetros, medidores)'),
-- ('Zona de Vertedouro', 'Estrutura para extravasamento controlado de água'),
-- ('Zona de Tomada d''Água', 'Estrutura para captação de água do reservatório'),

-- -- Zonas Adjacentes
-- ('Pé de Montante', 'Área adjacente ao talude de montante'),
-- ('Pé de Jusante', 'Área adjacente ao talude de jusante'),
-- ('Área de Borda do Reservatório', 'Margens do lago artificial formado pela barragem'),

-- -- Zonas Especiais
-- ('Zona de Núcleo Impermeável', 'Seção central com material de baixa permeabilidade'),
-- ('Zona de Transição', 'Camadas intermediárias entre núcleo e enrocamento'),
-- ('Zona de Enrocamento', 'Camada externa com material granular de maior granulometria');


-- ALTER TABLE tipos_materiais ADD COLUMN usuario_id INTEGER;

-- DROP TABLE IF EXISTS modos_falha_associacoes;

-- CREATE TABLE IF NOT EXISTS modos_falha (
--             id INTEGER PRIMARY KEY AUTOINCREMENT,
--             usuario_id INTEGER NOT NULL,
--             tipo_modo_falha_id INTEGER NOT NULL,
--             nome TEXT NOT NULL,
--             descricao TEXT
--             referencia_tecnica TEXT,
--             image_path TEXT  -- Caminho local ou URL da imagem associada
--         );


-- CREATE TABLE IF NOT EXISTS tipo_modo_falha (
--             id INTEGER PRIMARY KEY AUTOINCREMENT,
--             usuario_id INTEGER NOT NULL,
--             nome TEXT NOT NULL,
--             descricao TEXT,
--             referencia_tecnica TEXT
--          );

-- INSERT INTO tipo_modo_falha (usuario_id, nome, descricao, referencia_tecnica) VALUES
-- -- 1. Erosão Interna
-- (1, 'Erosão Interna', 'Erosão interna dos solos ou dos preenchimentos de descontinuidades nos encontros, fundação ou corpo do aterro, incluindo zonas próximas a condutas/galerias.', 'Caldeira, L. M. M. S. (2008). Análise de risco em geotecnia, aplicação a barragens de aterro. LNEC, p. 10'),

-- -- 2. Movimento de Grandes Massas
-- (1, 'Movimento de Grandes Massas', 'Instabilidades estáticas ou sísmicas (incluindo liquefação, assentamentos e perda de folga), galgamento por instabilidade de encostas ou ruptura por corte na fundação.', 'Caldeira, L. M. M. S. (2008). Análise de risco em geotecnia, aplicação a barragens de aterro. LNEC, p. 10'),

-- -- 3. Roturas Hidráulicas
-- (1, 'Roturas Hidráulicas', 'Falhas devido a níveis de água excepcionais: galgamento (por capacidade insuficiente ou erro operacional), erosão no dissipador de energia ou galgamento do canal do descarregador.', 'Caldeira, L. M. M. S. (2008). Análise de risco em geotecnia, aplicação a barragens de aterro. LNEC, p. 10');


-- DROP TABLE IF EXISTS modos_falha;
-- CREATE TABLE IF NOT EXISTS modos_falha (
--             id INTEGER PRIMARY KEY AUTOINCREMENT,
--             usuario_id INTEGER NOT NULL,
--             id_tipo_modo_falha,
--             nome TEXT NOT NULL,
--             descricao TEXT,
--             referencia_tecnica TEXT,
--             image_path TEXT 
--          );

-- INSERT INTO modos_falha (usuario_id, id_tipo_modo_falha, nome, descricao, referencia_tecnica, image_path) VALUES
-- -- Erosão Interna (id_tipo_modo_falha = 1)
-- (1, 1, 'Erosão no corpo do aterro', 'Erosão interna dos solos ou preenchimentos de descontinuidades no corpo do aterro, encontros ou fundação', 'Caldeira, L. M. M. S. (2008). Análise de risco em geotecnia, aplicação a barragens de aterro. LNEC', NULL),
-- (1, 1, 'Erosão ao longo de condutas', 'Erosão interna próxima a condutas (descarga de fundo, tomada de água) ou estruturas rígidas', 'Caldeira, L. M. M. S. (2008). Análise de risco em geotecnia, aplicação a barragens de aterro. LNEC', NULL),

-- -- Movimento de Grandes Massas (id_tipo_modo_falha = 2)
-- (1, 2, 'Instabilidade estática/sísmica', 'Instabilidade por ações estáticas (esvaziamento rápido) ou sísmicas nos maciços, fundação ou encontros', 'Caldeira, L. M. M. S. (2008). Análise de risco em geotecnia, aplicação a barragens de aterro. LNEC', NULL),
-- (1, 2, 'Assentamentos com perda de folga', 'Assentamentos que levam a galgamento e erosão externa', 'Caldeira, L. M. M. S. (2008). Análise de risco em geotecnia, aplicação a barragens de aterro. LNEC', NULL),
-- (1, 2, 'Liquefação sísmica', 'Liquefação do núcleo ou fundação devido a sismos', 'Caldeira, L. M. M. S. (2008). Análise de risco em geotecnia, aplicação a barragens de aterro. LNEC', NULL),
-- (1, 2, 'Rotura por corte na fundação', 'Falha em argilas plásticas com amolecimento por molhagem', 'Caldeira, L. M. M. S. (2008). Análise de risco em geotecnia, aplicação a barragens de aterro. LNEC', NULL),

-- -- Roturas Hidráulicas (id_tipo_modo_falha = 3)
-- (1, 3, 'Galgamento por capacidade insuficiente', 'Galgamento devido à incapacidade do descarregador de cheias', 'Caldeira, L. M. M. S. (2008). Análise de risco em geotecnia, aplicação a barragens de aterro. LNEC', NULL),
-- (1, 3, 'Galgamento por erro operacional', 'Falha no manejo de comportas do descarregador', 'Caldeira, L. M. M. S. (2008). Análise de risco em geotecnia, aplicação a barragens de aterro. LNEC', NULL),
-- (1, 3, 'Erosão no dissipador de energia', 'Erosão no canal ou bacia de dissipação do descarregador', 'Caldeira, L. M. M. S. (2008). Análise de risco em geotecnia, aplicação a barragens de aterro. LNEC', NULL),
-- (1, 3, 'Galgamento do canal do descarregador', 'Erosão externa da fundação/aterro por galgamento das paredes', 'Caldeira, L. M. M. S. (2008). Análise de risco em geotecnia, aplicação a barragens de aterro. LNEC', NULL);




-- DROP TABLE IF EXISTS modos_falha;
-- CREATE TABLE IF NOT EXISTS modos_falha (
--             id INTEGER PRIMARY KEY AUTOINCREMENT,
--             usuario_id INTEGER NOT NULL,
--             id_tipo_modo_falha INTEGER NOT NULL,
--             nome TEXT NOT NULL,
--             descricao TEXT,
--             referencia_tecnica TEXT,
--             image_path TEXT 
--          );

-- DROP TABLE IF EXISTS anomalias;
-- CREATE TABLE IF NOT EXISTS anomaliasx (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     usuario_id INTEGER NOT NULL,
--     nome TEXT NOT NULL,
--     descricao TEXT,
--     gravidade REAL,
--     peso REAL,
--     referencia_tecnica TEXT,
--     image_path TEXT
-- );

-- CREATE TABLE IF NOT EXISTS tipo_anomalia (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     usuario_id INTEGER NOT NULL,
--     nome TEXT NOT NULL,
--     descricao TEXT,
--     image_path TEXT
-- );



CREATE TABLE IF NOT EXISTS modos_falha (
--             id INTEGER PRIMARY KEY AUTOINCREMENT,
--             usuario_id INTEGER NOT NULL,
--             id_tipo_modo_falha INTEGER NOT NULL,
--             nome TEXT NOT NULL,
--             descricao TEXT,
--             referencia_tecnica TEXT,
--             image_path TEXT 
--          );



-- -- Relaciona modo do falha com tipo de barragem
-- CREATE TABLE IF NOT EXISTS modos_falha_tipo_barragem (
--     modos_falha_id INTEGER NOT NULL,
--     tipo_barragem_id INTEGER NOT NULL,
--     FOREIGN KEY (modos_falha_id) REFERENCES modos_falha(id),
--     FOREIGN KEY (tipo_barragem_id) REFERENCES tipos_barragem(id),
--     PRIMARY KEY (modos_falha_id, tipo_barragem_id)
-- );

-- CREATE TABLE IF NOT EXISTS tipo_modo_falha (
--             id INTEGER PRIMARY KEY AUTOINCREMENT,
--             usuario_id INTEGER NOT NULL,
--             nome TEXT NOT NULL,
--             descricao TEXT,
--             referencia_tecnica TEXT
--         );


-- CREATE TABLE IF NOT EXISTS tipo_anomalia (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     usuario_id INTEGER NOT NULL,
--     nome TEXT NOT NULL,
--     descricao TEXT,
--     image_path TEXT
-- );

-- DROP TABLE IF EXISTS anomalias;
-- -- Relaciona  modo de falha com as anomalias
-- CREATE TABLE IF NOT EXISTS anomalias (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     modos_falha_id INTEGER NOT NULL,           
--     usuario_id INTEGER NOT NULL,            
--     tipo_anomalia_id INTEGER NOT NULL,         
--     gravidade REAL,
--     peso REAL,
--     image_path TEXT,
--     FOREIGN KEY (modos_falha_id) REFERENCES modos_falha(id),
--     FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
--     FOREIGN KEY (tipo_anomalia_id) REFERENCES tipo_anomalia(id)
-- );

-- -- Relaciona anomalia com zona
-- CREATE TABLE IF NOT EXISTS anomalia_zona (
--     anomalia_id INTEGER NOT NULL,
--     zona_id INTEGER NOT NULL,
--     FOREIGN KEY (anomalia_id) REFERENCES anomalias(id),
--     FOREIGN KEY (zona_id) REFERENCES tipos_zonas_bar(id),
--     PRIMARY KEY (anomalia_id, zona_id)
-- );

-- -- Relaciona anomalia com tipo de material
-- CREATE TABLE IF NOT EXISTS anomalia_tipo_material (
--     anomalia_id INTEGER NOT NULL,
--     tipo_mat_id INTEGER NOT NULL,
--     FOREIGN KEY (anomalia_id) REFERENCES anomalias(id),
--     FOREIGN KEY (tipo_mat_id) REFERENCES tipos_materiais(id),
--     PRIMARY KEY (anomalia_id, tipo_mat_id)
-- );


-- DROP TABLE IF EXISTS anomalias_observadas;
-- --Registo de anomalias_observadas pelo usuário
-- CREATE TABLE IF NOT EXISTS anomalias_observadas (
--     id INTEGER PRIMARY KEY AUTOINCREMENT, 
--     barragem_id INTEGER NOT NULL,                      
--     tipo_anomalia_id INTEGER NOT NULL,         
--     tipos_zonas_bar_id INTEGER NOT NULL,  
--     tipos_materiais_id INTEGER NOT NULL,  
--     descricao TEXT,
--     image_path TEXT,

--     fonte_inspecao_visual BOOLEAN DEFAULT 0,
--     fonte_instrumentacao BOOLEAN DEFAULT 0,
--     fonte_drones BOOLEAN DEFAULT 0,
--     fonte_insar BOOLEAN DEFAULT 0,
--     fonte_satellite BOOLEAN DEFAULT 0,

--     data_observacao DATE,


--     FOREIGN KEY (barragem_id) REFERENCES barragens(id),
--     FOREIGN KEY (tipo_anomalia_id) REFERENCES tipo_anomalia(id),
--     FOREIGN KEY (tipos_zonas_bar_id) REFERENCES tipos_zonas_bar(id),
--     FOREIGN KEY (tipos_materiais_id) REFERENCES tipos_materiais(id)
-- );

DROP TABLE IF EXISTS zonas_barragem;







         