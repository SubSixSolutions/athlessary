time_example_str = """Fey I
v20:00f1:34r...3 Total T1me:
[NVI E FAT prac
t1me meter [500m 51n ®
“41143 9977 21040 17 _      BEE: FE EE5
[REC 12 105
20:000 4852 2:03.56 18 157
[rth EL pb
1:43 274 2:155 16 146
[gl1] 1]        5OLL]
"""

meter_example_str = """pr Deta1l
12000mTFB 1.
CIO a pa <  471238 12000 1.584 19         9:30.2 2400 1:58.7 18
932.3 4800 1:5%.3 18
9:33.93 7200 1:5%5 19
930.8 9600 1:58.9 20
9:16.0 12000 1:55.8 22     py54
"""


def text_post_process(erg_string, workout_type=None):
    erg_string = erg_string.lower().splitlines()
    digit_list = [0, 1, ]
    if workout_type is None:
        return None
    elif workout_type == 'meter':
        pass
    elif workout_type == 'time':
        workout_idx = -1
        for idx, line in enumerate(erg_string):
            if 'time' in line or 'meter' in line:
                workout_idx = idx + 1

        erg_string = erg_string[workout_idx].split(' ')
        if workout_idx >= 0:
            for info_idx, info in enumerate(erg_string):
                for char_idx, char in enumerate(info):
                    if not str.isdigit(char):
                        info = info[:char_idx] + info[char_idx + 1:]
                erg_string[info_idx] = info
        info_dict = {'time': erg_string[0], 'meters': erg_string[1], 'split': erg_string[2], 'spm': erg_string[3]}
        print(info_dict)
    else:
        return None