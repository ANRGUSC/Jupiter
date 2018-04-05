"""
Static assignments for testing the Jupiter system.
"""
dag=['localpro',
 {'aggregate0': ['1',
                 'true',
                 'simpledetector0',
                 'astutedetector0',
                 'dftdetector0',
                 'teradetector0'],
  'aggregate1': ['1',
                 'true',
                 'simpledetector1',
                 'astutedetector1',
                 'dftdetector1',
                 'teradetector1'],
  'aggregate2': ['1',
                 'true',
                 'simpledetector2',
                 'astutedetector2',
                 'dftdetector2',
                 'teradetector2'],
  'astutedetector0': ['1', 'true', 'fusioncenter0'],
  'astutedetector1': ['1', 'true', 'fusioncenter1'],
  'astutedetector2': ['1', 'true', 'fusioncenter2'],
  'dftdetector0': ['1',
                   'true',
                   'fusioncenter0',
                   'dftslave00',
                   'dftslave01',
                   'dftslave02'],
  'dftdetector1': ['1',
                   'true',
                   'fusioncenter1',
                   'dftslave10',
                   'dftslave11',
                   'dftslave12'],
  'dftdetector2': ['1',
                   'true',
                   'fusioncenter2',
                   'dftslave20',
                   'dftslave21',
                   'dftslave22'],
  'dftslave00': ['1', 'false', 'dftslave00'],
  'dftslave01': ['1', 'false', 'dftslave01'],
  'dftslave02': ['1', 'false', 'dftslave02'],
  'dftslave10': ['1', 'false', 'dftslave10'],
  'dftslave11': ['1', 'false', 'dftslave11'],
  'dftslave12': ['1', 'false', 'dftslave12'],
  'dftslave20': ['1', 'false', 'dftslave20'],
  'dftslave21': ['1', 'false', 'dftslave21'],
  'dftslave22': ['1', 'false', 'dftslave22'],
  'fusioncenter0': ['4', 'true', 'globalfusion'],
  'fusioncenter1': ['4', 'true', 'globalfusion'],
  'fusioncenter2': ['4', 'true', 'globalfusion'],
  'globalfusion': ['3', 'true', 'home'],
  'localpro': ['1', 'false', 'aggregate0', 'aggregate1', 'aggregate2'],
  'simpledetector0': ['1', 'true', 'fusioncenter0'],
  'simpledetector1': ['1', 'true', 'fusioncenter1'],
  'simpledetector2': ['1', 'true', 'fusioncenter2'],
  'teradetector0': ['1', 'true', 'fusioncenter0', 'teramaster0'],
  'teradetector1': ['1', 'true', 'fusioncenter1', 'teramaster1'],
  'teradetector2': ['1', 'true', 'fusioncenter2', 'teramaster2'],
  'teramaster0': ['1', 'false', 'teraworker00', 'teraworker01', 'teraworker02'],
  'teramaster1': ['1', 'false', 'teraworker10', 'teraworker11', 'teraworker12'],
  'teramaster2': ['1', 'false', 'teraworker20', 'teraworker21', 'teraworker22'],
  'teraworker00': ['1', 'false', 'teraworker00'],
  'teraworker01': ['1', 'false', 'teraworker01'],
  'teraworker02': ['1', 'false', 'teraworker02'],
  'teraworker10': ['1', 'false', 'teraworker10'],
  'teraworker11': ['1', 'false', 'teraworker11'],
  'teraworker12': ['1', 'false', 'teraworker12'],
  'teraworker20': ['1', 'false', 'teraworker20'],
  'teraworker21': ['1', 'false', 'teraworker21'],
  'teraworker22': ['1', 'false', 'teraworker22']},
 {'aggregate0': 'node33',
  'aggregate1': 'node31',
  'aggregate2': 'node18',
  'astutedetector0': 'node31',
  'astutedetector1': 'node29',
  'astutedetector2': 'node8',
  'dftdetector0': 'node6',
  'dftdetector1': 'node9',
  'dftdetector2': 'node20',
  'dftslave00': 'node11',
  'dftslave01': 'node23',
  'dftslave02': 'node23',
  'dftslave10': 'node33',
  'dftslave11': 'node24',
  'dftslave12': 'node22',
  'dftslave20': 'node8',
  'dftslave21': 'node31',
  'dftslave22': 'node13',
  'fusioncenter0': 'node30',
  'fusioncenter1': 'node8',
  'fusioncenter2': 'node35',
  'globalfusion': 'node33',
  'localpro': 'node4',
  'simpledetector0': 'node2',
  'simpledetector1': 'node21',
  'simpledetector2': 'node5',
  'teradetector0': 'node29',
  'teradetector1': 'node35',
  'teradetector2': 'node12',
  'teramaster0': 'node21',
  'teramaster1': 'node10',
  'teramaster2': 'node33',
  'teraworker00': 'node28',
  'teraworker01': 'node37',
  'teraworker02': 'node37',
  'teraworker10': 'node19',
  'teraworker11': 'node25',
  'teraworker12': 'node13',
  'teraworker20': 'node35',
  'teraworker21': 'node14',
  'teraworker22': 'node37'}]
schedule=['localpro',
 {'aggregate0': ['1',
                 'true',
                 'simpledetector0',
                 'astutedetector0',
                 'dftdetector0',
                 'teradetector0'],
  'aggregate1': ['1',
                 'true',
                 'simpledetector1',
                 'astutedetector1',
                 'dftdetector1',
                 'teradetector1'],
  'aggregate2': ['1',
                 'true',
                 'simpledetector2',
                 'astutedetector2',
                 'dftdetector2',
                 'teradetector2'],
  'astutedetector0': ['1', 'true', 'fusioncenter0'],
  'astutedetector1': ['1', 'true', 'fusioncenter1'],
  'astutedetector2': ['1', 'true', 'fusioncenter2'],
  'dftdetector0': ['1',
                   'true',
                   'fusioncenter0',
                   'dftslave00',
                   'dftslave01',
                   'dftslave02'],
  'dftdetector1': ['1',
                   'true',
                   'fusioncenter1',
                   'dftslave10',
                   'dftslave11',
                   'dftslave12'],
  'dftdetector2': ['1',
                   'true',
                   'fusioncenter2',
                   'dftslave20',
                   'dftslave21',
                   'dftslave22'],
  'dftslave00': ['1', 'false', 'dftslave00'],
  'dftslave01': ['1', 'false', 'dftslave01'],
  'dftslave02': ['1', 'false', 'dftslave02'],
  'dftslave10': ['1', 'false', 'dftslave10'],
  'dftslave11': ['1', 'false', 'dftslave11'],
  'dftslave12': ['1', 'false', 'dftslave12'],
  'dftslave20': ['1', 'false', 'dftslave20'],
  'dftslave21': ['1', 'false', 'dftslave21'],
  'dftslave22': ['1', 'false', 'dftslave22'],
  'fusioncenter0': ['4', 'true', 'globalfusion'],
  'fusioncenter1': ['4', 'true', 'globalfusion'],
  'fusioncenter2': ['4', 'true', 'globalfusion'],
  'globalfusion': ['3', 'true', 'home'],
  'localpro': ['1', 'false', 'aggregate0', 'aggregate1', 'aggregate2'],
  'simpledetector0': ['1', 'true', 'fusioncenter0'],
  'simpledetector1': ['1', 'true', 'fusioncenter1'],
  'simpledetector2': ['1', 'true', 'fusioncenter2'],
  'teradetector0': ['1', 'true', 'fusioncenter0', 'teramaster0'],
  'teradetector1': ['1', 'true', 'fusioncenter1', 'teramaster1'],
  'teradetector2': ['1', 'true', 'fusioncenter2', 'teramaster2'],
  'teramaster0': ['1', 'false', 'teraworker00', 'teraworker01', 'teraworker02'],
  'teramaster1': ['1', 'false', 'teraworker10', 'teraworker11', 'teraworker12'],
  'teramaster2': ['1', 'false', 'teraworker20', 'teraworker21', 'teraworker22'],
  'teraworker00': ['1', 'false', 'teraworker00'],
  'teraworker01': ['1', 'false', 'teraworker01'],
  'teraworker02': ['1', 'false', 'teraworker02'],
  'teraworker10': ['1', 'false', 'teraworker10'],
  'teraworker11': ['1', 'false', 'teraworker11'],
  'teraworker12': ['1', 'false', 'teraworker12'],
  'teraworker20': ['1', 'false', 'teraworker20'],
  'teraworker21': ['1', 'false', 'teraworker21'],
  'teraworker22': ['1', 'false', 'teraworker22']},
 {'aggregate0': ['aggregate0', 'rpi33', 'root', 'PASSWORD'],
  'aggregate1': ['aggregate1', 'rpi31', 'root', 'PASSWORD'],
  'aggregate2': ['aggregate2', 'rpi18', 'root', 'PASSWORD'],
  'astutedetector0': ['astutedetector0', 'rpi31', 'root', 'PASSWORD'],
  'astutedetector1': ['astutedetector1', 'rpi29', 'root', 'PASSWORD'],
  'astutedetector2': ['astutedetector2', 'rpi8', 'root', 'PASSWORD'],
  'dftdetector0': ['dftdetector0', 'rpi6', 'root', 'PASSWORD'],
  'dftdetector1': ['dftdetector1', 'rpi9', 'root', 'PASSWORD'],
  'dftdetector2': ['dftdetector2', 'rpi20', 'root', 'PASSWORD'],
  'dftslave00': ['dftslave00', 'rpi11', 'root', 'PASSWORD'],
  'dftslave01': ['dftslave01', 'rpi23', 'root', 'PASSWORD'],
  'dftslave02': ['dftslave02', 'rpi23', 'root', 'PASSWORD'],
  'dftslave10': ['dftslave10', 'rpi33', 'root', 'PASSWORD'],
  'dftslave11': ['dftslave11', 'rpi24', 'root', 'PASSWORD'],
  'dftslave12': ['dftslave12', 'rpi22', 'root', 'PASSWORD'],
  'dftslave20': ['dftslave20', 'rpi8', 'root', 'PASSWORD'],
  'dftslave21': ['dftslave21', 'rpi31', 'root', 'PASSWORD'],
  'dftslave22': ['dftslave22', 'rpi13', 'root', 'PASSWORD'],
  'fusioncenter0': ['fusioncenter0', 'rpi30', 'root', 'PASSWORD'],
  'fusioncenter1': ['fusioncenter1', 'rpi8', 'root', 'PASSWORD'],
  'fusioncenter2': ['fusioncenter2', 'rpi35', 'root', 'PASSWORD'],
  'globalfusion': ['globalfusion', 'rpi33', 'root', 'PASSWORD'],
  'home': ['home', 'rpi1', 'root', 'PASSWORD'],
  'localpro': ['localpro', 'rpi4', 'root', 'PASSWORD'],
  'simpledetector0': ['simpledetector0', 'rpi2', 'root', 'PASSWORD'],
  'simpledetector1': ['simpledetector1', 'rpi21', 'root', 'PASSWORD'],
  'simpledetector2': ['simpledetector2', 'rpi5', 'root', 'PASSWORD'],
  'teradetector0': ['teradetector0', 'rpi29', 'root', 'PASSWORD'],
  'teradetector1': ['teradetector1', 'rpi35', 'root', 'PASSWORD'],
  'teradetector2': ['teradetector2', 'rpi12', 'root', 'PASSWORD'],
  'teramaster0': ['teramaster0', 'rpi21', 'root', 'PASSWORD'],
  'teramaster1': ['teramaster1', 'rpi10', 'root', 'PASSWORD'],
  'teramaster2': ['teramaster2', 'rpi33', 'root', 'PASSWORD'],
  'teraworker00': ['teraworker00', 'rpi28', 'root', 'PASSWORD'],
  'teraworker01': ['teraworker01', 'rpi37', 'root', 'PASSWORD'],
  'teraworker02': ['teraworker02', 'rpi37', 'root', 'PASSWORD'],
  'teraworker10': ['teraworker10', 'rpi19', 'root', 'PASSWORD'],
  'teraworker11': ['teraworker11', 'rpi25', 'root', 'PASSWORD'],
  'teraworker12': ['teraworker12', 'rpi13', 'root', 'PASSWORD'],
  'teraworker20': ['teraworker20', 'rpi35', 'root', 'PASSWORD'],
  'teraworker21': ['teraworker21', 'rpi14', 'root', 'PASSWORD'],
  'teraworker22': ['teraworker22', 'rpi37', 'root', 'PASSWORD']}]
